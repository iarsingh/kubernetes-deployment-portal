def render(name, image, replicas):
    if ":" not in image or image.endswith(":latest"):
        raise ValueError("image tag latest is refused")
    if replicas < 1 or replicas > 5:
        raise ValueError("replicas must be from 1 to 5")
    return """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
spec:
  replicas: {replicas}
  template:
    spec:
      containers:
        - name: {name}
          image: {image}
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
""".format(name=name, image=image, replicas=replicas)
