# 01 Python Arb bot

This repo serves as a guide on how to use the Python SDK to run an arb on 01 and FTX.  
This repo SERVES ONLY AS A GUIDE and should not be run without using a burner wallet and understanding the associated risks.  
Please make sure you have read the code before running it as this code comes with no guarantees -- use at your own risk!

## Prerequisites

This is a Python 3.10 bot, with a couple dependencies.  
They can be installed with

```sh
$ pip install numpy zo-sdk ftx solana
```

Alternatively, if you use poetry, you can simply use

```sh
$ poetry install
```

The code imports many env variables, all of which are defined in [`.env.example`](./.env.example).  
All of these should be defined to run the bot, which can be done as so:

```sh
$ cp .env.example
# Fill out the variables
$ source .env
```

## Running

Now you're ready to run the bot.

```sh
$ poetry shell  # If you're using poetry
$ python run src/main.py
```
