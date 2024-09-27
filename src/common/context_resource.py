from src.common.data_models.models import Context
import json
import os
import falcon


class ContextResource(object):
    def on_post(self, req, resp):
        try:
            # Parse the JSON body
            body = req.media
            agent = body.get('agent')
            question = body.get('question')
            answer = body.get('answer')

            context = Context.create(agent=agent, question=question, answer=answer)
            context.save()

            # Respond with a success message
            resp.status = falcon.HTTP_200
            resp.text = json.dumps({"status": "success", "message": "Message stored successfully"})


        except Exception as e:
            # Handle unexpected errors
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": str(e)})