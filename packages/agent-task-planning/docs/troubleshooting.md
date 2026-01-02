# Troubleshooting

> Developed by [Members of the PDA Task Force](https://PDA Platform.co.uk) for the [PDA Task Force](https://github.com/PDATaskForce)

Common issues and solutions.

## Installation Issues

### Provider not found

**Error:** `ImportError: anthropic package not installed`

**Solution:**

```bash
pip install agent-task-planning[anthropic]
# or for all providers:
pip install agent-task-planning[all]
```

### Python version

**Error:** Various syntax errors

**Solution:** Requires Python 3.10+. Check: `python --version`

## Runtime Issues

### Guardrail violations

**Error:** `GuardrailViolation: Maximum iterations (50) exceeded`

**Solutions:**
1. Increase limits if appropriate
2. Check if the task is achievable
3. Add more specific instructions

### Task parsing failures

**Symptom:** Tasks not being created properly

**Solutions:**
1. Use a more capable model
2. Simplify the objective
3. Check max_tokens is sufficient

## Provider-Specific Issues

### Anthropic

**Error:** `anthropic.AuthenticationError`

**Solution:** Check API key: `echo $ANTHROPIC_API_KEY`

### Ollama

**Error:** Connection refused

**Solution:** Ensure Ollama is running: `ollama serve`

**Error:** Model not found

**Solution:** Pull the model: `ollama pull llama3.1:8b`

## Getting Help

1. Check existing [GitHub issues](https://github.com/PDATaskForce/agent-task-planning/issues)
2. Open a new issue with:
   - Python version
   - Library version
   - Provider being used
   - Minimal reproduction code
   - Full error traceback
