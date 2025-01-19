from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from typing import List, Dict, Tuple
import json
import os
import logging

from src.util_classes import Mutation, MutationLocation, MutationResult
from src.vars import GOOGLE_API_KEY

class MutationAssistant:
    def __init__(self, vector_store):
        """Initialize the mutation assistant with necessary components."""

        # Initialize logging
        self._logger = logging.getLogger(__name__)

        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3
        )

        self.system_prompt = """You are a mutation generator assistant for Java code. Your task is to generate code mutants based on given mutation operators. You will be provided with:

1.  **Source Code:** The primary Java code that you will mutate.
2.  **Helper Source Code:** Additional Java code that provides context but **must not be mutated**. This code may contain subclasses or related classes which give more information about the source code. The helper source code is provided to enhance your understanding of the project's structure and dependencies, allowing you to generate more contextually relevant and realistic mutants.
3.  **Mutation Operators:** A list of mutation operators, each described with its name, category, preconditions, description, and an example.

Your responsibilities are:

*   **Apply mutation operators ONLY to the Source Code.** You MUST NOT modify the Helper Source Code.
*   **Generate the mutant based on ONLY ONE valid mutation operator application.** Do not combine multiple mutation operators in one mutant. And DO NOT use the operator in multiple locations in a SINGLE MUTANT. But you are free to use the operator as much as possible in separate mutants.
*   **Output ONLY valid Java code.** The mutated code must compile and follow Java syntax.
*   **Your output must follow the specified JSON format
{
    "total_mutations": <number>,
    "mutations": [
        {
            "id": "M1",
            "operator": "<operator_name>",
            "mutated_code": "<full_mutated_source_code>",
            "location": {
                "line_number": <line_number>,
                "start_column": <optional_start>,
                "end_column": <optional_end>
            },
            "explanation": "<brief_explanation>"
        }
    ]
}

**Important Constraints:**

*   **Focus on the provided operators:** Do not generate mutations that are not explicitly described in the `mutation_operators`.
*   **Strictly adhere to the preconditions for each operator:** If preconditions are not met in the code, do not attempt to apply that mutation.
*   **Maintain code structure:**  Do not drastically change the structure of the code. Mutations should be localized as much as possible.
*   **The goal is to test the impact of small changes.** The mutations should be minimal to help isolate potential issues.
*   **Always output in JSON format. For long values of `mutated_code` DO NOT USE string concatination with plus operators. Put all the code inside 2 double-quotations and escape other special characters appropriately.**
*   **Ensure mutations are syntactically correct and compilable.** Provide the full mutant code and avoid partial code outputs. The code must be runnable.
*   **Make sure that full mutated source code (<full_mutated_source_code>) is something different with source code <src>, if it is not delete that mutation.**
"""
        self._vector_store = vector_store

        # Create the QA prompt template
        self.qa_template = """
        {system_prompt}

        Context from documentation:
        {context}

        Source Code:
        ```java
        {source_code}
        ```

        Helper Source Code:
        ```java
        {helper_source}
        ```

        Mutation Operators: {mutation_operators}

        Generate mutations and return them in the specified JSON format.
        """

        self.prompt = PromptTemplate(
            template=self.qa_template,
            input_variables=["system_prompt", "context", "source_code", "helper_source", "mutation_operators"]
        )

    def _get_relevant_documents(self, operator_names: List[str]) -> List:
        """Get relevant documents directly from the vector store using metadata filtering."""
        if not self._vector_store:
            raise ValueError("Vector store not initialized. Please set vector store first.")

        self._logger.info(f"Retrieving documents for operator names: {operator_names}")

        documents = self._vector_store.similarity_search(
            query=" ".join(operator_names),
            k=len(operator_names),
            filter={
                "op_name": {"$in": operator_names}
            }
        )

        return documents

    def _create_qa_chain(self):
        return create_stuff_documents_chain(llm=self.llm, prompt=self.prompt)

    def _parse_response(self, response_text: str, mutant_filepath: str) -> MutationResult:
        """Parse the LLM response into a MutationResult object"""
        try:
            # Checking if the response text is between ```json and ``` and extracting with regex
            import re
            match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if match:
                response_text = match.group(1)


            result_dict = json.loads(response_text)

            # Convert the dictionary to a MutationResult object
            mutations = []
            for mut in result_dict['mutations']:
                location = MutationLocation(
                    line_number=mut['location']['line_number'],
                    start_column=mut['location'].get('start_column'),
                    end_column=mut['location'].get('end_column')
                )

                file_stem = os.path.splitext(os.path.basename(mutant_filepath))[0]

                mutation = Mutation(
                    id=file_stem + "_" + mut['id'],
                    operator=mut['operator'],
                    mutated_code=mut['mutated_code'],
                    location=location,
                    explanation=mut['explanation']
                )
                mutations.append(mutation)

            return MutationResult(
                total_mutations=result_dict['total_mutations'],
                rel_path=mutant_filepath,
                mutations=mutations
            )

        except Exception as e:
            self._logger.error(f"Error parsing LLM response: {str(e)}")
            raise ValueError(f"Failed to parse LLM response: {str(e)}")
    def generate(self, source_code: str, helper_source: str, mutation_operators: List[str], mutant_filepath: str) -> Tuple[MutationResult, list]:
        """Answer a question using the RAG system."""
        context = self._get_relevant_documents(mutation_operators)

        self._logger.debug(f"Relevant documents: {context}")

        qa_chain = self._create_qa_chain()

        response = qa_chain.invoke({
            "context": context,
            "source_code": source_code,
            "helper_source": helper_source,
            "mutation_operators": mutation_operators,
            "system_prompt": self.system_prompt
        })

        self._logger.info(f"LLM response: {response}")

        return self._parse_response(response, mutant_filepath), context
