# ==============================================================================
# Makefile — Residential Power Audit · Spark Pipeline
# ==============================================================================
 
.PHONY: run test clean
 
NOTEBOOKS := notebooks
JUPYTER   := jupyter nbconvert --to notebook --execute --inplace
 
# Ejecuta el pipeline completo: ETL → H1 → H2 → H3 → H4
run:
	@echo "⚡ Running full pipeline..."
	$(JUPYTER) $(NOTEBOOKS)/00_ETL_Pipeline.ipynb
	$(JUPYTER) $(NOTEBOOKS)/01_H1_Load_Optimization.ipynb
	$(JUPYTER) $(NOTEBOOKS)/02_H2_Anomaly_Detection.ipynb
	$(JUPYTER) $(NOTEBOOKS)/03_H3_NILM_Standby.ipynb
	$(JUPYTER) $(NOTEBOOKS)/04_H4_Grid_Quality.ipynb
	@echo "✅ Pipeline complete. Outputs in data_storage/work/ and docs/"
 
# Lanza la suite de tests
test:
	@echo "🧪 Running test suite..."
	pytest tests/ -v
 
# Elimina cachés y artefactos temporales de Spark y Python
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__"        -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "spark-warehouse"    -exec rm -rf {} + 2>/dev/null || true
	find . -name "derby.log"                  -delete 2>/dev/null || true
	@echo "✅ Done."