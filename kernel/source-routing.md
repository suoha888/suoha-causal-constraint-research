# Source routing kernel

Route each question to the strongest appropriate source class. Do not treat five articles repeating one issuer announcement as five independent sources.

| Question | Preferred order |
| --- | --- |
| Security identity | regulator → exchange → issuer → licensed reference provider |
| Financials | regulatory filing → filed exhibit → audited statement → issuer IR → secondary database |
| Quote | exchange-authorized feed → licensed vendor → delayed feed → official close → `UNKNOWN` |
| Shares | latest filing plus subsequent issuance/repurchase filings → exchange corporate action → issuer → aggregator |
| Customer relationship | customer disclosure → procurement/contract record → customer announcement → supplier filing → issuer announcement → trade press → social lead |
| Capacity | permit/commissioning evidence → equipment evidence → filing → customer disclosure → issuer IR → specialist analysis |
| Policy | official regulator or government rule → standard body → specialist analysis → news |

Source perspective and independence group are stored with every record so source count does not become false corroboration.
