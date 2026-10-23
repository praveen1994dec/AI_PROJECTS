FROM debian:bullseye-slim AS builder
RUN apt-get update && apt-get install -y curl unzip tar

WORKDIR /downloads

# 1. Download Terraform
RUN curl -LO https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip && \
    unzip terraform_1.5.0_linux_amd64.zip

# 2. Download TFLint
RUN curl -L https://github.com/terraform-linters/tflint/releases/latest/download/tflint_linux_amd64.zip -o tflint.zip && \
    unzip tflint.zip

# 3. Download TFSec
RUN curl -L https://github.com/aquasecurity/tfsec/releases/latest/download/tfsec-linux-amd64 -o tfsec && \
    chmod +x tfsec

# 4. Download Infracost
RUN curl -L https://github.com/infracost/infracost/releases/latest/download/infracost-linux-amd64.tar.gz -o infracost.tar.gz && \
    tar -xzf infracost.tar.gz && \
    mv infracost-linux-amd64 infracost

# 5. Download GitHub CLI
RUN curl -L https://github.com/cli/cli/releases/download/v2.32.0/gh_2.32.0_linux_amd64.tar.gz -o gh.tar.gz && \
    tar -xzf gh.tar.gz && \
    mv gh_*_linux_amd64/bin/gh gh

FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Copy ONLY the compiled binaries from the builder stage
COPY --from=builder /downloads/terraform /usr/local/bin/
COPY --from=builder /downloads/tflint /usr/local/bin/
COPY --from=builder /downloads/tfsec /usr/local/bin/
COPY --from=builder /downloads/infracost /usr/local/bin/
COPY --from=builder /downloads/gh /usr/local/bin/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your actual application code
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]