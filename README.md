<!-- PROJECT LOGO -->
<!-- 
<br />
<div align="center">
  <a href="https://github.com/escomputers/BASD">
   <img src="templates/icon.ico" alt="Logo" width="80" height="80">
  </a>
-->

<h3 align="center">BASD</h3>
 <h6 align="center">acronym for</h6>
  <p align="center">
    Binance Automatic Stop Daemon
    <br />
    <br />
    ·
    <a href="https://github.com/escomputers/BASD/issues">Report Bug »</a>
    ·
    <a href="https://github.com/escomputers/BASD/issues">Request Feature »</a>
  </p>
</div>

<!-- DEMO -->
## Web demo (under dev)
<a href="https://emilianospada.pythonanywhere.com">Link hosted on Python Anywhere »</a>

<!-- WHY BASD -->
## Why BASD?
Binance is unquestionably the world greatest and most secure cryptocurrency exchange and many of us trade there.
For those like me that open and close positions within the same day or few hours, it's extremely important to carefully watch graphs to monitor price movements.

Sometimes (very often in my case) we cannot monitor price during a trade.
Expecially if an order is being filled during nightime, how can we place an order if we're sleeping, trekking or just working?

BASD solves the problem by constantly and securely listening to Binance account and if a BUY order is FILLED, it will automatically place a Stop Loss, Take Profit or OCO order basing on your choice.

BASD <ins><b>DOES NOT</ins></b> store or save or get your API keys. 
Keys are temporarily saved into your device RAM and after you close BASD, everything get deleted and you have to insert them again.
If you read source code line by line, there's no hidden treat.

<!-- Threat Intelligence Portal Analysis -->
#### Threat Intelligence Portal Analysis powered by ![Kaspersky][Kaspersky]
* [Ubuntu binary](https://opentip.kaspersky.com/8FC311547747145D046C3D31682049493510F8A3C183B481008011B03A82866F/results)
* [Windows binary](https://opentip.kaspersky.com/CA288B869C313BB67B295934C7373144FB84566A6F3A3E2F2C36939CE051DB5F/results)

<!-- Prerequisites -->
### Prerequisites
BASD requires <b>Binance.com API key and API secret key</b>. If you don't know how to create API keys, follow these [instructions](https://www.binance.com/en/support/faq/how-to-create-api-360002502072). Note that Binance.us is not currently supported.

<!-- GETTING STARTED -->
## Getting started

### Docker version
```docker pull escomputers/basd```

```docker run -e DJANGO_SECRET_KEY='' -dp 8000:8000 escomputers/basd```

### Binary version
For Windows and Ubuntu/Debian just download last stable binary file from [releases](https://github.com/escomputers/BASD/releases) page.
Extract zip archive and run BASD

Do not move or delete ```templates``` directory, otherwise it won't work!
* Tested on ![Windows][Windows]
* Tested on ![Ubuntu][Ubuntu]
* MacOS users can install [Parallels](https://www.parallels.com/it/) and then run BASD within it.

<!-- USAGE -->
## Usage
When program starts you will asked for these <ins>required</ins> parameters:
* Timezone continent + city <sup>1</sup>
* Start time <sup>2</sup>
* Number of active hours <sup>3</sup>
* Order type <sup>4</sup>
* Sell percentage <sup>5</sup>

<sup>1</sup> [Here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) you can find a complete list of all supported timezones, <b>e.g. Europe/Berlin</b>

<sup>2</sup> When you want program starts working, <b>e.g. 23:55</b>

<sup>3</sup> Number of active hours, used for end time calculation, <b>e.g. 8</b>

<sup>4</sup> Supported order types are <ins>only for sell</ins> side: [Take Profit](https://academy.binance.com/en/articles/what-is-a-stop-limit-order) - [Stop Loss](https://academy.binance.com/en/articles/what-is-a-stop-limit-order) - [OCO](https://academy.binance.com/en/articles/what-is-an-oco-order)

<sup>5</sup> BASD will calculate order sell price with your desired percentage, <b>e.g. 2.45</b>


You can optionally be notified whenever a job is started or order is placed. If you select "Email Alert", you will asked for:
- Sender Gmail address
- Gmail app password (<ins><b>not</b></ins> your Gmail password)
- Receiver email address

Note that only Gmail accounts are currently supported. Follow these [instructions](https://support.google.com/mail/answer/185833?hl=en), if you don't know how to create a Gmail application password.

When placing orders always <ins><b>REMEMBER</ins></b> these trading rules:
1. Binance will not accept any buy or sell order whose values is less than 11 USD
2. For OCO sell order, you must have the following price schema: Limit Price > Last Price > Stop Price. Last price <ins><b>is not</ins></b> symbol price when buy order is filled but it's symbol last price when sell order will be placed!

After you fill all required fields, another window will popup, just click ```Start``` and you're done, then first window can be safely closed.

<!-- CONTRIBUTING -->
## Contributing
Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

### If BASD was useful don't forget to give the project a [star](https://github.com/escomputers/BASD/stargazers)!


<!-- LICENSE -->
## License
Distributed under the Apache 2.0 License. See [license](https://github.com/escomputers/BASD/blob/GUI/LICENSE) for more information.


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[HTML]: https://img.shields.io/badge/HTML-239120?style=for-the-badge&logo=html5&logoColor=white
[HTML-url]: https://html.com/
[Linux]: https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black
[MacOS]: https://img.shields.io/badge/mac%20os-000000?style=for-the-badge&logo=macos&logoColor=F0F0F0
[Windows]: https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white
[Ubuntu]: https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white
[Kaspersky]: https://camo.githubusercontent.com/a8908b2f9c27f5d9f81f8bfa1d41dcefcb4e75046eaf21e0dcda2c59d4273380/68747470733a2f2f696d672e736869656c64732e696f2f7374617469632f76313f7374796c653d666f722d7468652d6261646765266d6573736167653d4b6173706572736b7926636f6c6f723d303036443543266c6f676f3d4b6173706572736b79266c6f676f436f6c6f723d464646464646266c6162656c3d
