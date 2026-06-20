import os
import re
from typing import Optional
import pandas as pd
from google import genai
from google.genai import types

class HybridDataBot:
    """
    HybridDataBot processes natural language queries against a dataset.
    Level 1: Rule-Based execution instantly computes standard requests (sum, mean, max, min, count) via Regex + Pandas.
    Level 2: Gemini API Fallback handles complex questions, trend analysis, and abstract insights.
    """
    def __init__(self, df: pd.DataFrame, findings_summary: str):
        self.df = df
        self.findings_summary = findings_summary
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        # Initialize Gemini API Client
        if self.api_key:
            self.client = genai.Client()
        else:
            self.client = None

        self._schema_str = self._generate_schema()

    def _generate_schema(self) -> str:
        """Create a string representation of the pandas dataframe schema for context."""
        schema = []
        for col, dtype in self.df.dtypes.items():
            schema.append(f"- '{col}': type {dtype}")
        
        sample = self.df.head(3).to_csv(index=False)
        return (
            "DataFrame Schema:\n" + "\n".join(schema) + 
            "\n\nSample Data (first 3 rows):\n" + sample
        )

    def _execute_rule_based(self, query: str) -> Optional[str]:
        """
        Level 1 Check:
        Match basic aggregation queries (e.g. "what is the sum of sales").
        If parsed correctly, performs the Pandas computation immediately.
        """
        query_lower = query.lower()
        
        # Regex map for common aggregations and column extractions
        agg_pattern = re.compile(r'\b(sum|mean|average|max|maximum|min|minimum|count)\b[^\w]*(?:of|for|on)?\s+(?:the\s+)?([a-zA-Z0-9_\s]+)', re.IGNORECASE)
        match = agg_pattern.search(query_lower)

        if match:
            operation = match.group(1).lower()
            raw_target = match.group(2).strip()

            # Map the operation text to a pandas function
            op_map = {
                'sum': 'sum',
                'mean': 'mean',
                'average': 'mean',
                'max': 'max',
                'maximum': 'max',
                'min': 'min',
                'minimum': 'min',
                'count': 'count'
            }
            pd_op = op_map.get(operation)

            # Look for the exact column name in the DataFrame
            # Try exact first, then lower case matching, then partial
            target_col = None
            df_cols = [c for c in self.df.columns]
            
            for col in df_cols:
                if col.lower() == raw_target:
                    target_col = col
                    break
            
            if not target_col:
                for col in df_cols:
                    if raw_target in col.lower() or col.lower() in raw_target:
                        target_col = col
                        break

            if target_col and pd_op:
                try:
                    # Execute Pandas Operation
                    if pd_op == "count":
                        result = self.df[target_col].count()
                    else:
                        result = getattr(self.df[target_col], pd_op)()
                        
                    # Format output nicely for floats vs ints
                    if isinstance(result, float):
                        formatted_result = f"{result:,.2f}"
                    else:
                        formatted_result = f"{result:,}"
                        
                    return f"**[Instant Computation]**: The {operation} of '{target_col}' is {formatted_result}."
                except Exception as e:
                    # Silently fallback to Gemini if Pandas operation fails (e.g. mean of categorical)
                    return None
                    
        return None

    def _execute_gemini_fallback(self, query: str) -> str:
        """
        Level 2 Check:
        Utilize Google Gemini SDK to intelligently digest the prompt using 
        the dataset schema and existing analytics summary as context.
        """
        if not self.client:
            return "Error: GEMINI_API_KEY is not configured. The AI cannot process this advanced query."

        # Setup the System Context Prompt
        system_instruction = (
            "You are a Senior Data Analyst AI embedded in the 'DataNarrate' platform.\n"
            "You are answering a user's question regarding an uploaded dataset.\n"
            f"{self._schema_str}\n\n"
            "Here is the pre-computed analytical findings summary over this data:\n"
            f"{self.findings_summary}\n\n"
            "Instructions:\n"
            "Provide clear, concise, and analytical answers. Format outputs using markdown. "
            "Use the provided summary and schema context to infer the best insights. Do not hallucinate data values."
        )

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                )
            )
            return response.text
        except Exception as e:
            return f"Error connecting to Gemini API: {str(e)}"

    def ask(self, user_query: str) -> str:
        """
        Main interface method. Tries Level 1 (Heuristics) first. 
        If no rules match, gracefully routes exactly to Level 2 (Gemini Fallback).
        """
        if not user_query.strip():
            return "Please provide a valid question."

        # Level 1: Heuristic Interception
        instant_response = self._execute_rule_based(user_query)
        if instant_response:
            return instant_response

        # Level 2: Deep LLM Reasoning
        return self._execute_gemini_fallback(user_query)

# Example usage string at EOF (Optional)
# if __name__ == "__main__":
#     import pandas as pd
#     df = pd.DataFrame({'Sales': [100, 200, 300], 'Region': ['NA', 'NA', 'EU']})
#     bot = HybridDataBot(df, findings_summary="Sales are booming overall.")
#     print(bot.ask("What is the sum of Sales?"))
#     print(bot.ask("What is the key trend here?"))
