# Workers' Compensation Knowledge Graph Demo: Operationalization & Testing Guide

This guide provides the exact, step-by-step instructions to operationalize the codebase locally, connect it to a Neo4j database, generate synthetic data, and test the functionality of the Streamlit application.

---

## Part 1: Infrastructure Setup (Neo4j AuraDB)

The application uses Neo4j to store the Knowledge Graph. It is designed to work within the limits of the **Neo4j AuraDB Free tier**.

1. Go to the [Neo4j Aura Console](https://console.neo4j.io/).
2. Sign in or create an account.
3. Click **"New Instance"** and select the **AuraDB Free** tier.
4. Name the instance (e.g., "WC-KG-Demo") and click **Create**.
5. **CRITICAL:** A `.txt` file containing your generated `password` will automatically download, and the credentials will be displayed on the screen. **Save this password**; it will not be shown again.
6. Wait 1-2 minutes for the instance status to change to "Running".
7. Note the **Connection URI** (it looks like `neo4j+s://xxxxxxxx.databases.neo4j.io`).

---

## Part 2: Local Configuration

Now, configure your local application to talk to the Neo4j instance.

1. Open your project directory: `c:\Users\admin\projects\kg-wc-temporal`.
2. Locate the file: `.streamlit/secrets.toml.example`.
3. Rename this file to `.streamlit/secrets.toml`.
4. Open the file and update it with your Neo4j URI and password from Part 1:
   ```toml
   [neo4j]
   uri = "neo4j+s://xxxxxxxx.databases.neo4j.io"  # Replace with your URI
   user = "neo4j"                                 # Default user is usually neo4j
   password = "your-password-here"                # Replace with your saved password
   ```

---

## Part 3: Environment Setup & Execution

1. Open a terminal or PowerShell window.
2. Navigate to the project directory:
   ```bash
   cd c:\Users\admin\projects\kg-wc-temporal
   ```
3. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```
5. A browser window will automatically open pointing to `http://localhost:8501`.

---

## Part 4: Data Generation & Testing (The Admin Page)

When the app opens, the database will be empty. You must generate the data using the Admin panel.

1. In the Streamlit sidebar, click on **Admin**.
2. **Step A:** Click the **"1. Clear Database"** button to ensure a clean slate. Wait for the success message.
3. **Step B:** Click the **"2. Generate Synthetic Data (~400 claims)"** button. 
   * *Testing Note:* This runs the `scenario_data_generator.py` script. It will take about 30 seconds to populate catalog nodes, entities, and ~400 deterministic temporal claim chains. Wait for the green success message.
4. **Step C:** Click the **"3. Compute Pairwise Similarity"** button.
   * *Testing Note:* This runs the `similarity_engine.py` script. It pulls all claims into memory, computes the Demographics + Shape + Pacing + Graph composite similarity for all pairs, and writes the top 15 matches back to Neo4j as `:SIMILAR_TO` edges. This takes about 60 seconds. Wait for the success message.
5. Review the **Database Statistics** table on the Admin page to confirm nodes (Claims, Persons, Stages, etc.) and relationships have been created.

---

## Part 5: Functional Testing of the UI

Now that the data is generated, you can test the primary demo flows.

### Test 1: Portfolio Overview
1. Navigate to the **Portfolio Overview** page via the sidebar.
2. **Verify KPIs:** Ensure the top metrics (Total Claims, Open Claims, Reserves, etc.) are populated.
3. **Verify Grid:** The "Claim Roster" table should be visible and filterable using the sidebar "Status" radio buttons.
4. **Deep Dive Test:**
   * Select a Claim ID from the dropdown below the grid.
   * **Verify Timeline:** A Plotly Gantt chart should render, showing the temporal stages of the claim.
   * **Verify Network:** A `streamlit-agraph` visual should render, showing the Claim connected to a Claimant, Employer, Adjuster, Attorney (if applicable), and Providers.

### Test 2: Similarity Workbench (The "Hero" Scenarios)
1. Navigate to the **Similarity Workbench** page via the sidebar.
2. **Select a Hero:** In the "Configuration" panel, use the dropdown to select one of the "Quick Select (Hero Scenarios)" (e.g., `CLM-HERO-01`).
3. **Verify Script:** A blue information box should appear containing the scripted demo narrative for that specific claim.
4. **Verify Dynamic Reweighting:** 
   * Play with the "Weight Preset" radio buttons (e.g., change from "Balanced" to "Shape-led").
   * **Result:** The "Top Similar Claims" table on the right should instantly re-rank the neighbors and update the Match % bars without needing to re-run the backend engine.
5. **Verify Trajectory Alignment:**
   * In the "Trajectory Alignment Comparison" section, select one of the neighbor claims from the dropdown.
   * **Result:** A dual-timeline chart should render, showing the Anchor claim's path directly above the Neighbor claim's path, allowing for visual comparison of where the claims aligned and where they diverged.

---

## Troubleshooting

* **Connection Errors:** If the app throws a Neo4j connection error, double-check your `.streamlit/secrets.toml` file. Ensure there are no spaces around the URI and the password is exact.
* **Empty Tables/Visuals:** If pages load but show no data, return to the Admin page and re-run Step 2 and Step 3. 
* **Missing Dependencies:** If `streamlit run app.py` fails with a `ModuleNotFoundError`, ensure you ran `pip install -r requirements.txt` in the correct Python environment.
