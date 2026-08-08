# Model comparison: simple instructions

Run these from the CAM_CAM checkout. Use the checkout-local module so an older
global `cam` install cannot be selected accidentally.

1. Put `OPENROUTER_API_KEY` in the ignored `.env` file.
2. Capture frozen, no-spend mining prompts:

   ```sh
   PYTHONPATH=src python -m claw.cli models benchmark fixtures \
     benchmarks/mining-v1.toml \
     --repo-root /path/to/repos \
     --config claw.toml \
     --output data/model_benchmarks/my-run/fixtures.json
   ```

3. Create the no-spend plan and confirm it is under your cap:

   ```sh
   PYTHONPATH=src python -m claw.cli models benchmark plan \
     benchmarks/mining-v1.toml \
     --fixtures data/model_benchmarks/my-run/fixtures.json \
     --budget-usd 5 \
     --output data/model_benchmarks/my-run
   ```

4. Run exact models with no fallback:

   ```sh
   PYTHONPATH=src python -m claw.cli models benchmark run \
     data/model_benchmarks/my-run/plan.json \
     --fixtures data/model_benchmarks/my-run/fixtures.json \
     --output data/model_benchmarks/my-run \
     --budget-usd 5 --no-fallback
   ```

5. Generate the report:

   ```sh
   PYTHONPATH=src python -m claw.cli models benchmark report \
     data/model_benchmarks/my-run \
     --fixtures data/model_benchmarks/my-run/fixtures.json \
     --format markdown \
     --output data/model_benchmarks/my-run/report.md
   ```

Do not select a model unless it has the required quality score and no hard
failures. The benchmark never changes the active profile automatically.

