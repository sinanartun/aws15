FROM public.ecr.aws/lambda/python:3.11

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt --only-binary=:all:

COPY model.pkl .
COPY lambda_function.py .

CMD ["lambda_function.lambda_handler"]
