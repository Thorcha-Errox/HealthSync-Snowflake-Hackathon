# HealthSync: Inventory Heatmap & Stock-Out Alerts

**HealthSync** is a unified inventory intelligence platform built on Snowflake. It helps hospitals and NGOs prevent critical supply shortages by visualizing stock health and predicting stock-outs before they happen.

## 🚀 Key Features
* **Real-time Heatmap:** Instantly spot locations with low stock.
* **Smart Alerts:** Automated 'Critical' and 'Warning' flags based on lead time and usage rate.
* **Actionable Insights:** Auto-generates procurement lists for immediate download.

## 🛠️ Tech Stack
* **Database:** Snowflake (Data Storage)
* **Transformation:** Snowflake Dynamic Tables (Automated Logic)
* **Application:** Streamlit in Snowflake (Python Dashboard)
* **Visualization:** Altair

## 📂 Repository Structure
* `app.py`: The Python code for the Streamlit Interface.
* `setup.sql`: The SQL scripts to set up the Database, Warehouse, and Dynamic Tables.

## 📸 How to Run
1.  Run the scripts in `setup.sql` in a Snowflake Worksheet.
2.  Create a Streamlit App in Snowflake and paste the code from `app.py`.
3.  Run the app to see the dashboard.
