# Saturn and MediaMarkt Monitor

A simple monitor in Pyhton that using the **Backend APIs** of MediaMarkt (MMS) and Saturn allows you to monitor the availability of specific products via link/pid or keywords.
It can easily be converted to other languages. During drops could activate the Cloudflare challenge, the helheim support is already implemented and the hawk support can easily be implemented. 
There's already proxy support and Discord webhook support. 
I made this script for testing purposes, feel free to adapt and modify it.

# Table of contents

- [Installation](#installation)
- [Usage](#usage)
    - [Run](#run)
    - [Manage Database](#manage-database)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [Contact me](#contact-me)

# Installation

```
py -m pip install -r requirements.txt
```

# Usage

## Run

[(Back to top)](#table-of-contents)

Start Saturn monitor by running `py main.py saturn` or MediaMarkt via `py main.py mms`. 
If you don't know what helheim is or don't have it, run always with `--no-helheim`

### Flags

- With `--proxyless` : You'll run the script proxyless by ignoring the `proxy.txt` file

- With `--no-helheim` : You'll not run the script using helheim (suggested if not installed)

- With `--no-kws` : You'll run only the specific links/pids monitor

## Manage Database

[(Back to top)](#table-of-contents)

The database is managed via sql and you can find it inside the db folder. I left the PID of an iPhone for both sites to allow some quick tests. You can edit it using any suitable editor or via the commands in the database.py file.
For each pid within the restock collection, a monitor thread will be started, same for keywords.
```
py database.py {site} {type} {target}
``` 

### Examples

- Add a pid to Saturn's database

```
py database.py saturn pid 2664075
```
- Add multiple pids to MediaMarkt's database
```
py database.py mms pid 2664075,2664074
```
- Same thing for keywords
```
py database.py mms kws "play station 5,iphone 14"
```

### Flags

- With `--remove` : Add at the end of the command in order to remove the targets from the db.
    
    ```
    py database.py mms kws "play station 5,iphone 14"

    py database.py saturn kws "play station 5" --remove
    ```

# Configuration

[(Back to top)](#table-of-contents)

The settings.json file will allow you to select Discord webhook, delay and hawk settings to be used.
The delay is in milliseconds, I suggest setting this based on if/how many proxies you are using (just enter them in the proxy.txt file one per line in the format ip:port or ip:port:user:passw) and if you are using helheim or any other solution for Cloudflare.
Remember tof ille the helheim part in order to use it.

![image](https://i.imgur.com/s8az74n.png)

# Contributing

[(Back to top)](#table-of-contents)

Your contributions are always welcome!

# Contact me

[Mail](mailto:glizzykingdreko@protonmail.com) | [Twitter](https://twitter.com/glizzykingdreko)