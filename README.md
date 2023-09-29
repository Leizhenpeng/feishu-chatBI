# Feishu DataGPT (Code Interpreter)

Welcome to Feishu DataGPT, a Code Interpreter integration with Feishu. This project attempts to seamlessly integrate [Code Interpreter](https://github.com/shroominic/codeinterpreter-api) into the Feishu platform. In this demo, we leverage a non-open source [Codebox](https://github.com/shroominic/codebox-api/tree/main) for executing Python code. Future updates will include our in-house Codebox.

## Demo

Our integration offers interactive capabilities within Feishu documents (ensure your bot has the necessary permissions). It also supports document and file uploads.

### Interaction with Feishu Docs
![Feishu Document Interaction](imgs/feishu_file.gif)

### Creating Python Plots
![Python Plotting](imgs/plot.gif)

## Deploying the Server with Docker

### Environment Configuration

### Launching Docker
```shell
docker-compose -f docker_dev.yml build
docker-compose -f docker_dev.yml up
```

Feel free to explore our Feishu DataGPT integration further. If you have any questions or need assistance, please don't hesitate to reach out.
