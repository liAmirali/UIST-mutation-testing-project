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
            model="gemini-1.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.5
        )

        self.system_prompt = """You are a mutation generator assistant for Java code. Your task is to generate code mutants based on given mutation operators. You will be provided with:

1.  **Source Code:** The primary Java code that you will mutate.
2.  **Helper Source Code:** Additional Java code that provides context but **must not be mutated**. This code may contain subclasses or related classes which give more information about the source code. The helper source code is provided to enhance your understanding of the project's structure and dependencies, allowing you to generate more contextually relevant and realistic mutants.
3.  **Mutation Operators:** A list of mutation operators

Your responsibilities and constraints:

*   **Apply all applicable mutation operators to every possible location in the source code.** You must use one mutation operator from the given operators list each time.
*   **Apply mutation operators ONLY to the Source Code.** You MUST NOT modify the Helper Source Code.
*   **Mutate and GENERATE the NEW source code based on the applied operator** MAKE SURE to change the corresponding line
*   **Generate the mutant based on ONLY ONE valid mutation operator application.** Do not combine multiple mutation operators in one mutant. And DO NOT use the operator in multiple locations in a SINGLE MUTANT. But you are free to use the operator as much as possible in separate mutants.
*   **Output ONLY valid Java code.** The mutated code must compile and follow Java syntax.
*   **Use the inheritance description to understand the project structure.** This information will help you identify the classes and interfaces that are part of the project.
*   **Focus on the provided operators:** Do not generate mutations that are not explicitly described in the `mutation_operators`.
*   **Strictly adhere to the preconditions for each operator:** If preconditions are not met in the code, DO NOT attempt to apply that mutation. If the operator is not applicable, simply SKIP it.
*   **Do not generate redundant mutations.** If a mutation doesn't apply to the source code, SKIP the operator and do not generate a mutation of that operator.
*   **Maintain code structure:**  Do not drastically change the structure of the code. Mutations should be localized as much as possible.
*   **The goal is to test the impact of small changes.** The mutations should be minimal to help isolate potential issues.
*   **Always output in JSON format.** Simply ESCAPE any double quotations inside the mutated source code (<full_mutated_source_code>).
*   **Do NOT use string concatenation (`+` operator).*** The code inside `mutated_code` should be output as a complete block, not pieced together using `+`
*   **Ensure mutations are syntactically correct and compilable.** Provide the full mutant code and avoid partial code outputs. The code must be runnable.
*   **Make sure that full mutated source code (<full_mutated_source_code>) is something different with source code <src>, if it is not delete that mutation.**
*   **DO NOT consider the mutations on Helper Source Code** If a mutation was applicable on the Helper Source Code, it is NOT VALID MUTATION.
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

        The project inheritance structure is also defined as such:
        {inheritance_desc}

        Mutation Operators: {mutation_operators}

        Generate mutations and return them in the specified JSON format.
        """

        self.prompt = PromptTemplate(
            template=self.qa_template,
            input_variables=["system_prompt", "context", "source_code", "helper_source", "inheritance_desc", "mutation_operators"]
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

    def generate(self, source_code: str, helper_source: str, inheritance_desc: str, mutation_operators: List[str], mutant_filepath: str) -> Tuple[MutationResult, list]:
        """Answer a question using the RAG system."""
        context = self._get_relevant_documents(mutation_operators)

        self._logger.debug(f"Relevant documents: {context}")

        qa_chain = self._create_qa_chain()

        response = qa_chain.invoke({
            "context": context,
            "source_code": source_code,
            "inheritance_desc": inheritance_desc,
            "helper_source": helper_source,
            "mutation_operators": mutation_operators,
            "system_prompt": self.system_prompt
        })

        self._logger.debug(f"LLM response: {response}")

        return self._parse_response(response, mutant_filepath), context
