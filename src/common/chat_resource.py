import json
import os
import falcon


class ChatResource(object):
    def on_post(self, req, resp):
        try:
            # Parse the JSON body
            body = req.media
            username = body.get('username')
            message = body.get('message')

            if not message or not username:
                raise ValueError("Missing 'username' or 'message' in request body")

            # Path to the JSON file where messages are stored
            file_path = 'assistant/llm_context.json'

            # Load existing data (if the file exists)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
            else:
                data = []

            # Append the new message object to the array
            data.append({"username": username, "message": message})

            # Write the updated data back to the file in JSON format
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)

            # Respond with a success message
            resp.status = falcon.HTTP_200
            resp.text = json.dumps({"status": "success", "message": "Message stored successfully"})


        except Exception as e:
            # Handle unexpected errors
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": str(e)})