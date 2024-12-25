FROM python:3.12.2

WORKDIR /app

# Install Doppler CLI
RUN apt-get update && apt-get install -y apt-transport-https ca-certificates curl gnupg && \
    curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] https://packages.doppler.com/public/cli/deb/debian any-version main" | tee /etc/apt/sources.list.d/doppler-cli.list && \
    apt-get update && \
    apt-get -y install doppler

COPY requirements.txt .

RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY src/ ./src

EXPOSE 5000

CMD ["doppler", "run", "--", "gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "--timeout", "240", "src.app:app"]
