from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from typing import List, Dict, Tuple
import json
import logging

from src.util_classes import MutationOperatorSelection
from src.vars import GOOGLE_API_KEY

class OperatorSelector:
    """Collects mutation operators from a user prompt."""

    def __init__(self, vector_store):
        # Initialize logging
        self._logger = logging.getLogger(__name__)

        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            api_key=GOOGLE_API_KEY,
            temperature=0.7
        )

        self.system_prompt = """You are an expert in software testing, specifically in mutation testing. Your role is to assist users in selecting appropriate mutation operators to achieve their specific testing goals. You will be provided with the user's prompt which explains their purpose and goals for conducting mutation testing.

            Your primary task is to analyze the user's prompt and provide a concise list of mutation operators that are most relevant to their needs.
            A list of operators is provided as the context. Select the most relevant ones from them according to the user needs. All of them might not be relevant.

            **Instructions:**

            1.  **Understand the User's Goal:** Carefully analyze the user's prompt to identify the underlying purpose of their mutation testing. What specific aspects of their code or system are they trying to target? Are they focused on specific programming paradigms (like inheritance or polymorphism), code smells, or particular types of defects?
            2.  **Utilize Provided Knowledge (RAG):** You have access to a knowledge base containing information about various mutation operators, their categories, descriptions, and use cases. Prioritize this information to make accurate recommendations.
            3.  **Prioritize Relevant Operators:** Based on your analysis, select mutation operators that directly address the user's goals. For instance:
                *   If the user is focusing on inheritance, operators like IHI, IHD, IOD, IOP, IOR, ISI, ISD and IPC would be relevant.
                *   If the user is focusing on polymorphism, operators like PNC, PMD, PPD, PCI, PCD, PPC, PRV, OMR, OMD, and OAC would be relevant.
                *   If the user is targeting encapsulation related defects AMC would be relevant.
                *   If the user is focused on Java-specific features, operators like JTI, JTD, JSI, JSD, JID, and JDC would be relevant.
            4.  **Provide a Structured Output:** Respond with a list of recommended mutation operators, formatted as a JSON array. Each object in the array should contain the `operator_name` (short code) and the `reason` why you chose that operator.
                ```json
                [
                {
                    "operator_name": <operator_name>,
                    "reason": <brief_explanation>
                },
                    ...
                ]
                ```

            5. **Explain your reasoning**: In each item of the JSON array, provide a very short explanation of why you chose each mutation operator. It should be brief and to the point.

            **Example:**

            **User Prompt:**
            "I want to test the robustness of my Java code's inheritance structure and make sure that overriding and hiding is working as I intend. Please recommend mutation operators to help with this."

            **Your Response:**
            ```json
            [
            {
                "operator_name": "IHI",
                "reason": "This operator tests how hiding of variables in inheritance behaves by inserting hiding variables."
            },
            {
                "operator_name": "IHD",
                "reason": "This operator checks if the code will still work as expected when hiding variables are deleted."
            },
            {
                "operator_name": "IOD",
                "reason": "This operator tests the behavior when a method is overridden, by deleting it."
            },
            {
                "operator_name": "IOP",
                "reason": "This operator tests the impact of changing the `super` call within a method."
            },
            {
                "operator_name": "IOR",
                "reason": "This operator verifies correct method calls are made when overriding methods are renamed."
            },
            {
                "operator_name": "ISI",
                "reason": "This operator tests the behavior when the `super` keyword is inserted."
            },
            {
                "operator_name": "ISD",
                "reason": "This operator tests the behavior when the `super` keyword is deleted."
            },
            {
                "operator_name": "IPC",
                "reason": "This operator checks the consequence of removing explicit calls to the parent constructor."
            }
            ]
            ```

            **Important Notes:**

            *   **Be Concise:** Your response should be succinct and easy to understand. Avoid verbose explanations unless absolutely necessary.
            *   **Be Accurate:** Prioritize accuracy and relevance over providing a large number of options.
            *   **Focus on Goals:** Always keep the user's intended goal in mind when selecting the most appropriate mutation operators.
            *   **Assume Basic Knowledge:** You can assume the user has a basic understanding of mutation testing and related concepts.
            *   **RAG Usage:** Rely heavily on the provided knowledge base to enhance the selection process. Do not generate operators or descriptions that are not in your knowledge base.

            By following these guidelines, you will effectively assist users in applying the correct mutation operators for their specific testing needs.
        """

        self._vector_store = vector_store

        # Create the QA prompt template
        self.qa_template = """
        {system_prompt}

        Context from documentation:
        {context}

        User prompt:
        My goal of testing is to {input}

        Generate correct mutation operators based on the user prompt and the given instructions in the given JSON structure as your software testing role.
        """

        self.prompt = PromptTemplate(
            template=self.qa_template,
            input_variables=["system_prompt", "context", "source_code", "mutation_operators"]
        )

    def _get_retriever(self):
        """Set up the retriever with the vector store."""
        if not self._vector_store:
            raise ValueError("Vector store not initialized. Please set vector store first.")

        return self._vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 10
            }
        )

    def _create_qa_chain(self, retriever):
        """Create the question-answering chain."""
        qa_chain = create_stuff_documents_chain(llm=self.llm, prompt=self.prompt)
        chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=qa_chain)

        return chain

    def _parse_response(self, response: Dict) -> List[MutationOperatorSelection]:
        """Parse the LLM response into a MutationResult object"""

        try:
            # Extract the response text and parse it as JSON
            response_text = response['answer']

            # Checking if the response text is between ```json and ``` and extracting with regex
            import re
            match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if match:
                response_text = match.group(1)


            operators_selected = json.loads(response_text)

            # Convert the dictionary to a MutationResult object
            operators = []
            for op in operators_selected:
                operators.append(
                    MutationOperatorSelection(
                        operator_name=op['operator_name'],
                        reason=op['reason']
                    )
                )

            return operators

        except Exception as e:
            self._logger.error(f"Error parsing LLM response: {str(e)}")
            raise ValueError(f"Failed to parse LLM response: {str(e)}")

    def generate(self, user_prompt: str) -> Tuple[List[MutationOperatorSelection], Dict]:
        """Answer a question using the RAG system."""
        retriever = self._get_retriever()

        qa_chain = self._create_qa_chain(retriever)

        response = qa_chain.invoke({
            "input": user_prompt,
            "system_prompt": self.system_prompt
        })

        self._logger.info(f"LLM response: {response}")

        return self._parse_response(response), response
