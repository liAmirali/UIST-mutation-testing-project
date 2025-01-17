from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from typing import List, Dict
import json
import logging

from src.output_classes import Mutation, MutationLocation, MutationResult
from src.vars import GOOGLE_API_KEY

class MutationAssistant:
    def __init__(self, google_api_key: str, vector_store):
        """Initialize the mutation assistant with necessary components."""

        # Initialize logging
        self._logger = logging.getLogger(__name__)

        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=google_api_key,
            temperature=0.3
        )

        self.system_prompt = """
        You are an expert mutation testing tool. Your task is to analyze Java source code and generate valid mutations based on provided mutation operators.

        You must return mutations in the following structured format without any markdown styling code:
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
            ],
            "applied_operators": ["<operator1>", "<operator2>", ...]
        }

        Instructions:
        1. Apply all applicable mutation operators to every possible location in the source code
        2. Ensure mutations are syntactically correct and compilable. Provide the full mutant code and avoid partial code outputs. The code must be runnable.
        3. Do not generate redundant mutations. Only one mutation should be generated for each operator per applicable location.
        4. Include line numbers for each mutation
        5. Provide brief but clear explanations
        6. Return a valid JSON object matching the above structure
        7. If no mutations are possible, return an object with total_mutations: 0 and empty arrays
        8. Ensure each operator is applied exactly once by selecting one valid mutation for it.

        Your response must be ONLY the JSON object - no additional text or explanations or stylings```.
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
        Mutation Operators: {mutation_operators}

        Generate mutations and return them in the specified JSON format.
        """

        self.prompt = PromptTemplate(
            template=self.qa_template,
            input_variables=["system_prompt", "context", "source_code", "mutation_operators"]
        )

    def _get_relevant_documents(self, operator_names: List[str]) -> List:
        """Get relevant documents directly from the vector store using metadata filtering."""
        if not self._vector_store:
            raise ValueError("Vector store not initialized. Please set vector store first.")

        self._logger.info(f"Retrieving documents for operator names: {operator_names}")
        
        documents = self._vector_store.similarity_search(
            query="",  # Empty query since we're only using metadata filtering
            k=len(operator_names),
            filter={
                "op_name": {"$in": operator_names}
            }
        )
        
        return documents

    def _create_qa_chain(self):
        return create_stuff_documents_chain(llm=self.llm, prompt=self.prompt)

    def _parse_response(self, response_text: str) -> MutationResult:
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
                mutation = Mutation(
                    id=mut['id'],
                    operator=mut['operator'],
                    mutated_code=mut['mutated_code'],
                    location=location,
                    explanation=mut['explanation']
                )
                mutations.append(mutation)

            return MutationResult(
                total_mutations=result_dict['total_mutations'],
                mutations=mutations,
                applied_operators=result_dict['applied_operators']
            )

        except Exception as e:
            self._logger.error(f"Error parsing LLM response: {str(e)}")
            raise ValueError(f"Failed to parse LLM response: {str(e)}")

    def generate(self, source_code: str, mutation_operators: List[str]) -> Dict:
        """Answer a question using the RAG system."""
        context = self._get_relevant_documents(mutation_operators)

        self._logger.debug(f"Relevant documents: {context}")

        qa_chain = self._create_qa_chain()

        response = qa_chain.invoke({
            "context": context,
            "source_code": source_code,
            "mutation_operators": mutation_operators,
            "system_prompt": self.system_prompt
        })

        self._logger.info(f"LLM response: {response}")

        return self._parse_response(response), context
