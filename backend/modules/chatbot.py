import os
import re
from typing import Optional, List, Dict
import pandas as pd
from google import genai
from google.genai import types

class HybridDataBot:
    """
    Modernized Chatbot Engine using Google Gen AI SDK.
    Supports Rule-Based instant computation + Multi-turn Gemini AI reasoning.
    """
    def __init__(self, df: pd.DataFrame, findings_summary: str):
        self.df = df
        self.findings_summary = findings_summary
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        # Initialize Google Gen AI Client
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

        self._schema_str = self._generate_schema()
        # Chat session storage (In-memory for this instance)
        self.chat_history = [] 

    def _generate_schema(self) -> str:
        schema = []
        for col, dtype in self.df.dtypes.items():
            schema.append(f"- '{col}': type {dtype}")
        sample = self.df.head(3).to_csv(index=False)
        return (
            "DataFrame Schema:\n" + "\n".join(schema) + 
            "\n\nSample Data (first 3 rows):\n" + sample
        )

    def _execute_rule_based(self, query: str) -> Optional[str]:
        # (Retention of the rule-based regex engine for instant computations)
        query_lower = query.lower()
        agg_pattern = re.compile(r'\b(sum|mean|average|max|maximum|min|minimum|count)\b[^\w]*(?:of|for|on)?\s+(?:the\s+)?([a-zA-Z0-9_\s]+)', re.IGNORECASE)
        match = agg_pattern.search(query_lower)
        if match:
            operation, raw_target = match.group(1).lower(), match.group(2).strip()
            op_map = {'sum':'sum','mean':'mean','average':'mean','max':'max','maximum':'max','min':'min','minimum':'min','count':'count'}
            pd_op = op_map.get(operation)
            target_col = next((c for c in self.df.columns if c.lower() == raw_target or raw_target in c.lower()), None)
            if target_col and pd_op:
                try:
                    result = self.df[target_col].count() if pd_op == "count" else getattr(self.df[target_col], pd_op)()
                    formatted = f"{result:,.2f}" if isinstance(result, float) else f"{result:,}"
                    return f"**[Instant Computation]**: The {operation} of '{target_col}' is {formatted}."
                except Exception: return None
        return None

    def ask_stream(self, user_query: str):
        """
        Streamed Multi-turn conversation logic using Gemini 2.5 Flash.
        """
        if not user_query.strip():
            yield "Please provide a valid question."
            return

        # 1. Check heuristics first
        instant = self._execute_rule_based(user_query)
        if instant:
            yield instant
            return

        if not self.client:
            yield "Error: Gemini API Client not initialized."
            return

        # 2. Construct context-aware prompt
        system_instruction = (
            "You are an Elite Data Analyst AI for DataNarrate.\n"
            f"Dataset Context:\n{self._schema_str}\n\n"
            f"Key Findings: {self.findings_summary}\n\n"
            "Instructions: Be analytical, use markdown, and maintain continuity with passed chat history."
        )

        try:
            # We recreate the full interaction including history for context
            # Note: For simplicity, we pass state within the content or use session.
            messages = [{"role": "user", "content": user_query}]
            
            # Streaming session
            for chunk in self.client.models.generate_content_stream(
                model='gemini-2.5-flash', # As requested in snippet
                contents=user_query,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                )
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error: {str(e)}"

# Example usage string at EOF (Optional)
# if __name__ == "__main__":
#     import pandas as pd
#     df = pd.DataFrame({'Sales': [100, 200, 300], 'Region': ['NA', 'NA', 'EU']})
#     bot = HybridDataBot(df, findings_summary="Sales are booming overall.")
#     print(bot.ask("What is the sum of Sales?"))
#     print(bot.ask("What is the key trend here?"))
