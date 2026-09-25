# Zepto Data & AI Platform Capstone

## Setup and Execution
1. Install dependencies: `pip install -r requirements.txt`
2. **Module 1 (Data Pipeline)**: Run `data_pipeline/pipeline.ipynb` to scrape data, build the SQLite database, and execute SQL queries.
3. **Module 2 (Analytics)**: Run `analytics/01_eda.ipynb` first to generate `titanic.csv`, followed by `analytics/02_modeling.ipynb` to train the models and save the pipeline artifact.
4. **Module 3 (Support Assistant)**: Run `python support_assistant/app.py` (or via Docker) to start the FastAPI server on port 7860.

---

## Module 1: Data Pipeline
* **Currency Conversion**: The baseline fixed-rate conversion used is exactly **1 GBP = 105.50 INR**.
* **Design**: The scraped data is cleaned and loaded into a normalized SQLite database with two tables (`categories` and `books`) sharing a Primary Key / Foreign Key relationship.

---

## Module 2: Analytics Pipeline
* **Missing Values**: Columns with <5% missing data (`embarked`, <1%) were dropped. Columns with 5-30% missing data (`age`, ~20%) were median-imputed. Columns with >30% missing data (`deck`, ~77%) were dropped entirely to prevent unreliable imputation.
* **Outliers**: Using the IQR rule, Age had 11 outliers and Fare had 116 outliers.
* **Skewness**: Fare is right-skewed because its Mean (32.20) is greater than its Median (14.45), which is greater than its Mode (8.05).
* **Correlations**: The two strongest numeric correlations observed were between `pclass` and `fare` (-0.55), and between `pclass` and `age` (-0.37).
* **Chart Interpretations**:
  1. *Survival by Sex*: Females survived at a significantly higher rate than males, indicating rescue protocols heavily prioritized women.
  2. *Survival by Passenger Class*: First-class passengers had the highest survival rate, showing a strong socio-economic factor in evacuation priority.
  3. *Age Distribution*: Young children had higher survival rates compared to middle-aged adults, aligning with the "women and children first" maritime protocol.
  4. *Fare vs Survival*: Higher ticket fares strongly correlate with better survival chances, reinforcing the advantage of higher passenger classes.
* **Imbalance Handling**: Comparing baseline, class weights, and SMOTE, the `class_weight='balanced'` strategy yielded the best practical balance, improving recall for the minority class without the severe overfitting risks introduced by SMOTE on this specific dataset.
* **Final Model Recommendation**: I recommend deploying the Random Forest classifier because it achieved the best overall balance of Accuracy (~81%) and F1 Score (~75%), capturing complex non-linear relationships in the data better than Logistic Regression.

---

## Module 3: Support Assistant
* **RAG Architecture**: 
  * **Ingestion & Embedding**: Handled by `sentence-transformers` (`all-MiniLM-L6-v2`), chunking the 8 policy text files.
  * **Retrieval**: Vector embeddings are stored and queried using a local `ChromaDB` collection.
  * **Generation**: Handled by a `LangGraph` StateGraph router that directs the query. 
  * **MOCK_LLM Branching**: The generation stage branches on the `MOCK_LLM` environment variable. In the default mock state, generation returns deterministic, canned template answers. If toggled to 0, it calls a real LLM.
* **Example JSON Responses (Mock Mode)**:
  * *Policy Query ("What is the return policy?")*: 
    ```json
    {
      "answer": "Based on the retrieved context: Grocery and perishable items may be reported for a return within 24 hours...",
      "sources": ["doc_02.txt"],
      "confidence": 1.0
    }
    ```
  * *General Query ("What is the weather?")*: 
    ```json
    {
      "answer": "I can only answer questions about Zepto policies right now.",
      "sources": [],
      "confidence": 1.0
    }
