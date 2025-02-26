# Didnodb - A Simple NoSQL Database

Didnodb is a lightweight NoSQL database implemented in Python using FastAPI. It provides user authentication, data storage, and basic CRUD operations without requiring a traditional database management system.

## Features
- User authentication (register, login, logout)
- Store and retrieve structured JSON data
- Session-based authentication
- Data indexing for faster retrieval
- Basic metrics for tracking users and stored data

## Installation
```sh
# Clone the repository
git clone https://github.com/yourusername/didnodb.git
cd didnodb

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

## Running the Server
```sh
uvicorn main:didnodb --reload
```

## API Endpoints
### User Authentication
- **Register a new user**  
  `POST /register`
  ```json
  {
    "username": "user1",
    "password": "securepassword"
  }
  ```

- **Login**  
  `POST /login`
  ```json
  {
    "username": "user1",
    "password": "securepassword"
  }
  ```

- **Logout**  
  `POST /logout`

### Data Management
- **Save Data**  
  `POST /data`
  ```json
  {
    "data": {
      "key": "value"
    }
  }
  ```

- **Get Specific Data**  
  `GET /data/{model_id}`

- **Get All User Data**  
  `GET /data`

- **Delete Data**  
  `DELETE /data/{model_id}`

### Other Endpoints
- **Check Server Status**  
  `GET /`
- **Get Metrics (Users & Stored Data Count)**  
  `GET /metrics`

## Database Structure
- User data is stored in `db/data/{username}`
- Each data entry is stored as a JSON file `{model_id}.json`

## Roadmap
- Implement indexing for faster queries
- Add support for data expiration (TTL)
- Improve security (hashed sessions, rate limiting)
- Introduce query filters

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to your branch (`git push origin feature-name`)
5. Open a Pull Request

## License
MIT License

---
Made with ❤️ by Deyan Sirakov