import json
import os
from venv import logger
import falcon


class FileResource(object):
    def on_post(self, req, resp):
        try:
            form_data = req.get_media()
            for part in form_data:
                if part.name == 'file':
                    file_name = part.filename
                    file_content = part.stream.read() # Gets text that is sent to this

            if file_content is None:
                resp.status = falcon.HTTP_400
                resp.text = json.dumps({"error": "File is required"})
                return
        
            file_path = os.path.join('/tmp', file_name)
            
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Respond with success message
            resp.status = falcon.HTTP_200
            resp.text = json.dumps({"status": "File uploaded successfully", "file_name": file_name})

        except Exception as e:
            # Handle unexpected errors
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": str(e)})