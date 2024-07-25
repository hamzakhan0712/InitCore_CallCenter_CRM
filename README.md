# CRM Project

A Customer Relationship Management (CRM) system built with Django.

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/hamzakhan0712/InitCore_CallCenter_CRM/
    ```

2. **Create and activate a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1. **Update `settings.py`** to use environment variables:
    ```python
    SET THE ENVIROMENTAL VARIABKE AND THE POSTGRESS USERNAME AND PASSWORD 

    SET THE EMAIL AND PASSWORD TOO FOR SENDING THE MAIL FROM THE COMPANY SIDE


    ```

## Running the Application

1. **Apply database migrations**:
    ```bash
    python manage.py migrate
    ```

2. **Create a superuser**:
    ```bash
    python manage.py createsuperuser
    ```

3. **Run the development server**:
    ```bash
    python manage.py runserver
    ```

4. **Access the application**:
    Open your web browser and go to `http://localhost:8000`.

## Testing

1. **Run tests**:
    ```bash
    python manage.py test
    ```

## Deployment

1. **Collect static files**:
    ```bash
    python manage.py collectstatic
    ```

2. **Configure your web server** (e.g., Gunicorn, Nginx) to serve the Django application.You have to setup Websocket and daphne too for prodcution it uses asgi.py whereas the regular produciton uses wsgi.py

3. **Set up environment variables** in your production environment.

4. **Run database migrations** and create a superuser in the production environment.

