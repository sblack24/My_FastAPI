FROM python:3.9

WORKDIR /src

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080:8080

CMD [ "python", "-m" , "main"]