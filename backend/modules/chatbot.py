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

    def _execute_gemini_fallback_stream(self, query: str):
        """
        Level 2 Check (Streaming):
        Utilize Google Gemini SDK (Gemini 3.5 Flash) to stream text tokens chunk-by-chunk.
        """
        if not self.client:
            yield "Error: GEMINI_API_KEY is not configured."
            return

        system_instruction = (
            "You are an Elite Data Narrator and Financial Analyst AI.\n"
            "Answering user questions regarding their dataset.\n"
            f"{self._schema_str}\n\n"
            "Findings Summary:\n"
            f"{self.findings_summary}\n\n"
            "Format: Use strict markdown. Provide deep statistical insights. Be concise but insightful. Standardize on the Gemini 3.5 Flash model."
        )

        try:
            for chunk in self.client.models.generate_content_stream(
                model='gemini-3.5-flash',
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.4,
                )
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error connecting to Gemini API: {str(e)}"

    def ask_stream(self, user_query: str):
        """
        Main streaming interface. Returns a generator yielding text chunks.
        """
        if not user_query.strip():
            yield "Please provide a valid question."
            return

        # Level 1: Heuristic Interception (Not streamed)
        instant_response = self._execute_rule_based(user_query)
        if instant_response:
            yield instant_response
            return

        # Level 2: Stream from Gemini 3.5 Flash
        yield from self._execute_gemini_fallback_stream(user_query)

# Example usage string at EOF (Optional)
# if __name__ == "__main__":
#     import pandas as pd
#     df = pd.DataFrame({'Sales': [100, 200, 300], 'Region': ['NA', 'NA', 'EU']})
#     bot = HybridDataBot(df, findings_summary="Sales are booming overall.")
#     print(bot.ask("What is the sum of Sales?"))
#     print(bot.ask("What is the key trend here?"))
