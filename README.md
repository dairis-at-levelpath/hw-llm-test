## How to run

1. Copy `.env.example` to `.env` and add the OPENAI_API_KEY.
  - Optional: you can change the `MODEL_NAME` to use a different model, remember to update `PRICE_PER_TOKEN` to match the new model (for token price calculations).
1. Add the homework source files in the `homework_source_code` directory.
2. Run the following command in the root directory of the project:

```bash
./bin/hw_eval
```

## How to configure inputs and outputs

### Prompts

The prompt templates are located in `prompt_templates` folder.

Files defined in `context_file_patterns.txt` are included in the context prompt.
Files defined in `ignore_file_patterns.txt` are ignored in the context prompt.

### Outputs

The outputs are saved in `result.md` in the root directory of the project.
The output templates are located in `output_templates` folder.
