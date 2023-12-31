<h1 align="center">🧑‍🚀 Fleet Code Pilot</h1>

<p align="center">
    <img src="https://img.shields.io/static/v1?label=license&message=MIT&color=white&style=flat" alt="License"/>
    <a href="https://discord.gg/YTc98S77aZ"><img src="https://img.shields.io/discord/1107887761412870154?logo=discord&style=flat&logoColor=white" alt="Discord"/></a>
    <br>
    <br>
    <b>A Github bot that automatically responds to issues using real-time data from your library's documentation, source code, & past issues.</b>
    <br>
    <span>View the demo over Pydantic's documentation: https://github.com/fleet-ai/issues-responder/issues/5</span>
    <br>
    <br>
    <a href="https://github.com/fleet-ai/context">Original Project</a>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <a href="https://x.com/fleet_ai">@fleet_ai</a>‎
    <br>
    <br>
    <br>
</p>

## Setup Guide

You'll need several things before we get set up.

1. A Pinecone account. Make one [here](https://pinecone.io).
2. An OpenAI account. Make one [here](https://platform.openai.com).
3. Embeddings. We already have support for embeddings covering the top 1221 libraries.

   You can check if your library is supported [here](https://fleet.so/context).
   If it's supported, you'll be able to get this set up pretty quickly.
   If it's not, you'll have to embed your documentation yourself. Luckly, [we have a full guide for you to follow](https://fleet.so/blog).

<br>

### 1. Set up your API

We will be using ngrok to set up your FastAPI endpoints, but feel free to use any alternatives. If you want to deploy this and put it in production, we recommend a more production-ready solution like AWS EC2 or similar.

First, clone this repository and install all requirements:

```shell
git clone https://github.com/fleet-ai/code-pilot.git
cd code-pilot
pip install -r requirements.txt
python main.py
```

Then, in a separate terminal window, follow the [ngrok quickstart guide](https://ngrok.com/docs/getting-started/) and run:

```shell
ngrok http 8000
```

This will set up web forwarding — any requests that go through ngrok will forward to your localhost server.

<br>

### 2. Create a Github bot

First, you'll need to create a new Github bot. Click on your profile on the top right corner of Github, then click `Settings` -> `Developer Settings` (should be the bottom option on the left sidebar). You should be greeted with this screen:

<img width="600" alt="Screenshot 2023-11-14 at 12 41 19 PM" src="https://github.com/fleet-ai/issues-responder/assets/44193474/03df90c8-48cd-4398-8e2c-861840597fb2">

Fill out the form with the right details, or leave it as the default value. Insert your ngrok URL you got from the previous section into the `Webhook URL`:

<img width="400" alt="Screenshot 2023-11-14 at 12 48 15 PM" src="https://github.com/fleet-ai/issues-responder/assets/44193474/4834d77d-f166-4c2f-9f3c-2507a5212ce3">

Under "Permissions", make sure you allow "Read and write" for issues. This is the only one you'll need.

<img width="400" alt="Screenshot 2023-11-14 at 12 49 20 PM" src="https://github.com/fleet-ai/issues-responder/assets/44193474/1d8dd788-7e27-4caf-b27d-63c14046f939">

You'll also want to subscribe to the `Issues` and `Issue comment` events so that your API is properly notified.

<img width="400" alt="Screenshot 2023-11-14 at 12 50 07 PM" src="https://github.com/fleet-ai/issues-responder/assets/44193474/caf5d808-ba1c-4e02-9001-f1d9444af46d">

Once you fill these out, click Create!

<br>

### 3. Generating your Github private key

Once you're done creating your bot, you should get a notification prompting you to create a Github private key. Go ahead and click that, then click "Generate Private Key". It should download a .pem file for you automatically.

<img width="400" alt="Screenshot 2023-11-14 at 12 52 03 PM" src="https://github.com/fleet-ai/issues-responder/assets/44193474/8a37fbf4-c5ae-454c-ba41-c898a0da77c6">

Drag and drop your .pem file into the root directory of the cloned `code-pilot` repository. We will be JWT and this .pem file to get a Github access token.

<br>

### 4. Set up services

#### OpenAI

Create a new file in the root directory called `.env` and add the line:

```
OPENAI_API_KEY=<your openai api key>
```

#### Pinecone

Now, you need to create a new Pinecone index. Follow Pinecone's instructions on how to do that. The pod that you use doesn't matter too much and depends on if you want to optimize for storage or performance. We recommend dotproduct as your metric, as we will be implementing a hybrid retrievals system.

Go to `constants.py` and update the following constants:

1. `INDEX_NAME`: the name of your index.
2. `INDEX_ENVIRONMENT`: the environment for your index (ie "us-east-1-aws")
3. `NAMESPACE`: the namespace you will be using within the index. Feel free to keep it blank.

In your .env file, add the line:

```
PINECONE_API_KEY=<your pinecone api key>
```

#### Github

Go to `constants.py` and update the following constants:

1. `APP_ID`: your Github app's ID. You can find it under the "General" tab within your app settings
2. `BOT_NAME`: whatever you want to name your bot
3. `PRIVATE_KEY_PATH`: the name of the .pem file you just added to your root directory

<br>

#### Source code

1. `PATH_TO_SRC_CODE`: the path to the root directory of the source code you want scraped. Must start with `src_code/` as that's where source code will be cloned into. If you don't change this, it will by default scrape your entire repository (which you may not always want).

<br>

### 4. Run and upsert your embeddings

#### Embedding documentation

Using Fleet's `context` module, we've written a script to automatically download and upsert your library's embeddings to Pinecone. Simply run:

```shell
make docs library_name=<your library name>
```

Check your Pinecone index to make sure everything was properly upserted.

You can view all supported libraries and their associated library names [here](https://fleet.so/context). If your library is not supported by Fleet Context out of the box, you can embed your documentation yourself using [our guide](https://fleet.so/blog) and continue through this tutorial once you've completed that.

<br>

#### Embedding source code

Regardless of whether or not your library is supported by Fleet Context out of the box, you'll be able to embed your source code so that your bot can reference it. Simply run:

```shell
make code url=<git clone link, i.e. https://github.com/pydantic/pydantic.git>
```

The script will clone the repository, scrape/chunk/embed the source code, then upsert it into your Pinecone index.

<br>

#### Embedding past issues

Install the app to your repository. You should see that it starts an asynchronous job to embed all past issues. Wait for this to finish. Tada, you have your past issues embedded!

Real-time issues embeddings are automatically supported. Every time a new issue is created, it automatically chunks and embeds it so that the bot always has real-time information about your library.

<br>

### 5. Test!

Open an issue and ask a question. It should give you a response with the right context.

Congratulations, you've set up your own issues responder bot!
