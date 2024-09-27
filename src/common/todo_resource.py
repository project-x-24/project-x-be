from src.common.data_models.models import ToDoList
import json
import falcon


class ToDoResource(object):
    def on_post(self, req, resp):
        try:
            # Parse the JSON body
            body = req.media
            event = body.get("event")
            date = body.get("date")

            context = ToDoList.create(event=event, date=date)
            context.save()

            # Respond with a success message
            resp.status = falcon.HTTP_200
            resp.text = json.dumps(
                {"status": "success", "message": "To do stored successfully"}
            )

        except Exception as e:
            # Handle unexpected errors
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": str(e)})

    def on_get(self, req, resp):
        try:
            entries = list(ToDoList.select(ToDoList.event, ToDoList.date))
            resp.status = falcon.HTTP_200
            resp.text = json.dumps({"items": [entry.__data__ for entry in entries]})

        except Exception as e:
            # Handle unexpected errors
            resp.status = falcon.HTTP_500
            resp.text = json.dumps({"error": str(e)})
