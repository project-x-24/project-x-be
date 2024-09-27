import json
import falcon


class ChatResource(object):
    def on_post(self, req, resp):
        try:
            # Parse the JSON body
            body = req.media
            message = body.get('message')
            
            if not message:
                raise ValueError("Missing 'message' in request body")

            # Path to the file where messages are appended
            file_path = 'assistant/llm_context.txt'

            # Open the file in append mode and write the message
            with open(file_path, 'a') as f:
                f.write(message + '\n')

            # Respond with a success message
            resp.status = falcon.HTTP_200
            resp.text = json.dumps({"status": "success", "message": "Success"})

        except Exception as e:
            # Handle unexpected errors
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": str(e)})