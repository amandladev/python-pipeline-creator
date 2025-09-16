# Pipeline Creator CLI

A CLI tool for creating and managing CI/CD pipelines on AWS quickly and easily.

## 🚀 Installation

### Development mode (recommended)

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
source .venv/bin/activate  # Mac/Linux
# or
.venv\Scripts\activate     # Windows

# 3. Install in development mode
pip install -e .
```

### Install from PyPI (coming soon)
```bash
pip install pipeline-creator
```

## 📋 Available Commands

### `pipeline init`
Initialize pipeline configuration in your repository.

```bash
pipeline init
```

### `pipeline generate`
Generate infrastructure files using AWS CDK.

```bash
pipeline generate
```

### `pipeline deploy`
Execute deployment with CDK.

```bash
pipeline deploy
```

### `pipeline status`
Show current pipeline status.

```bash
pipeline status
```

### `pipeline logs`
Show logs from the latest deployment.

```bash
pipeline logs
```

## 🛠️ Prerequisites

- Python 3.8+
- AWS CLI configured (`aws configure`)
- Node.js (for AWS CDK)

## 📁 File Structure

After running `pipeline init`, the following will be created:

```
.pipeline/
  config.json    # Pipeline configuration
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=pipeline_creator
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.
