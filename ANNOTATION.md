# Annotation guide

These rules decide where a span starts and ends and which label it gets. They follow
EverestNER wherever it has a clear habit, so that its labels and ours can be trained
together. The counts below are from the EverestNER training file.

The rules were written for Nepali. Release 0.2 adds seven labels and English, Hindi and
romanised Nepali; what that changes is in the last three sections. A rule stated for Nepali
holds for the other languages unless one of those sections says otherwise.

## Labels

| Label | Covers |
|---|---|
| `PERSON` | Names of people: full, given only, family only, initials with a family name |
| `LOCATION` | Named places: countries, provinces, districts, local levels, toles, streets, chowks, airports |
| `ORGANIZATION` | Named organisations: banks, offices, companies, schools, hospitals, parties |
| `DATE` | A calendar day, month or year in Bikram Sambat or the Common Era |
| `PHONE` | Mobile and landline numbers |
| `EMAIL` | E-mail addresses |
| `URL` | Web addresses, with or without `http` |
| `USERNAME` | Handles and login names |
| `IP_ADDRESS` | IPv4 and IPv6 addresses |
| `CITIZENSHIP_NO` | Citizenship certificate number of Nepal |
| `NATIONAL_ID` | National identity number: Nepal's NIN, Aadhaar, the social security number of the United States |
| `TAX_ID` | Tax number: PAN and VAT in Nepal (one number), PAN and GSTIN in India, EIN and TIN. Called `PAN` in release 0.1 |
| `PASSPORT_NO` | Passport number |
| `LICENSE_NO` | Driving licence number |
| `VOTER_ID` | Voter identity number |
| `ID_NUMBER` | Another number that names one person or their device: employee, student, roll, symbol, customer, patient, policy, IMEI |
| `BANK_ACCOUNT` | Bank account number, IBAN |
| `CARD_NUMBER` | Payment card number |
| `UPI_ID` | Payment address of the form `name@bank` |
| `VEHICLE_PLATE` | Vehicle registration number |
| `SECRET` | Passwords, keys, tokens, one-time codes, PINs |

## Where a span ends

1. **Case markers and particles stay outside.** In `अनिलकी`, the span is `अनिल`. The same holds
   for `ले को का की मा लाई बाट सँग देखि सम्म हरू पनि मात्र समेत स्थित द्वारा` and for the honorific
   endings `ज्यू` and `जी`. In EverestNER 61% of entities have such a suffix attached.
2. **Titles and kinship words stay outside**: `डा.`, `श्री`, `प्रधानमन्त्री`, `Mr.`, `sir`, `दाइ`, `didi`.
   EverestNER never starts a person span with a title.
3. **A type word that belongs to the name stays inside**: `नबिल बैंक`, `वीर अस्पताल`,
   `त्रिभुवन विश्वविद्यालय`, `पोखरा महानगरपालिका`, `लेखनाथ मार्ग`, `भानुचोक`, `कर्णाली प्रदेश`.
4. **`जिल्ला` stays outside**: `[दोलखा] जिल्ला` (30 of 30 cases in EverestNER).
5. **Ward numbers stay outside**: `[बनेपा नगरपालिका]-७`.
6. **A number is marked without its keyword**: in `नागरिकता नं. १२३४५` the span is `१२३४५`. A phone
   number includes its country code.

## Dates

A date is marked when it names a specific calendar day, month or year: `२०५१/०१/२३`,
`2053-08-08`, `असार २१`, `२०७२ भदौ ७`, `15 January 1994`.

- The era word and `साल` are inside: `सन् १९८८`, `वि.सं. २०७६`, `२०६३ साल`.
- `गते` and `तारिख` are outside: `[असार २१] गते` (271 outside, 46 inside in EverestNER).
- Not dates here: `आज`, `हिजो`, weekdays, a month alone, durations (`३ वर्ष`), ages
  (`९० वर्षकी`), times of day. EverestNER marks all of these as dates; they are removed when
  the training data is prepared, which keeps 884 of 3,399 date spans.

## Places and organisations

- A local level in an address is a `LOCATION`, with its type word. EverestNER labels every
  `नगरपालिका` as an organisation; the training data takes the label of a place when a ward number follows
  (104 cases).
- A local level acting as a body (`नगरपालिकाले निर्णय गर्‍यो`) is an `ORGANIZATION`.
- A place name inside an organisation name is part of the organisation:
  `[काठमाडौं विश्वविद्यालय]`. A person's name inside a place or organisation name is not a
  person: `[पृथ्वीनारायण क्याम्पस]`, `[भानुचोक]`.

## Words that are also names

`आशा`, `सागर`, `पूजा`, `प्रकाश`, `विश्वास`, `शान्ति`, `माया`, `नेपाल`, `श्रेष्ठ` and many others are
both ordinary words and names. Mark them only where they name a person or place.

## Settled while labelling real news

These came up in `real-news-v0` (2026-11-13). The counts are from the EverestNER training
file. Where two cuts are listed as accepted, the scorer takes either.

- **A word for a kind of body is not a name.** `प्रदेशसभा`, `जिल्ला प्रहरी कार्यालय`, `प्रादेशिक अस्पताल`,
  `प्रहरी` and `सरकार` are marked only with the word that tells which one: `[मधेश प्रदेशसभा]`,
  `[जिल्ला प्रहरी कार्यालय पर्सा]`. EverestNER leaves `प्रदेशसभा` unmarked in 29 of 30 cases and never
  marks `जिल्ला प्रहरी कार्यालय` on its own (9 cases, all unmarked). A body there is only one of is a name:
  `[सर्वोच्च अदालत]`.
- **A short form keeps its mark when it keeps a word of the name**: `[एमाले]`, `[दि हाइट]`.
- **A short form in brackets after an organisation is part of its span**:
  `[नेपाल कम्युनिष्ट पार्टी (एमाले)]`, `[राष्ट्रिय स्वतन्त्र पार्टी (रास्वपा)]` (68 cases in EverestNER, never
  two spans). Two spans are accepted. After a place, mark the two apart.
- **Places joined by a hyphen are marked one by one**: `[नेपाल]-[भारत] सीमा`. EverestNER makes
  one span of the pair in 52 of 53 cases, so one span is accepted.
- **A unit named after its parent** (`नेपाल प्रहरीको केन्द्रीय समाचार कक्ष`) is two spans or one;
  EverestNER has both (10 and 27).
- **A genitive splits a date**: `[२०८० साल]को [वैशाख ३१] गते`. One span is accepted.
- **A year written with three digits is a date**: `[०६४] देखि [०७९] सम्म`.
- **A team called by the name of its city is an organisation**: `[पोखरा]ले १३२ रन बनायो`.
- **Leagues and tournaments are events and are not marked** (`नेपाल प्रिमियर लिग`, `आईपीएल`;
  23 of 25 in EverestNER are events). The same holds for festivals.
- **Words for a people or a language are not places**: `नेपाली`, `भारतीय`, `जापानी`.
- **Brands, products, films and books are not marked.**
- **Stadiums and halls are places. Hospitals, prisons and police offices are organisations.**
- **A province is a place**: `[मधेश प्रदेश]का मुख्यमन्त्री`. EverestNER labels provinces as
  organisations in 65 of 67 cases; since release 0.1 the training data takes the label of a
  place, unless the province acts as a body.
- **A local level that could be read as a place or as a body** (three municipalities that
  sent fire engines) is accepted under either label.

## Settled before labelling the second news set

Fixed on 2026-11-13, before `real-news-v1` was labelled, from counts in the EverestNER
training file. They fill gaps the guide had left.

- **Type words inside a place name**: `बजार`, `राजमार्ग`, `नदी`, `खोला`, `ताल`, `मन्दिर`, `पार्क`,
  `चोक`, `टोल`, `गाउँ`, `उपत्यका`, `विमानस्थल`, `रंगशाला`, `मैदान`, `किल्ला` (`[त्रिशूली नदी]`, 16 of 19;
  `[चरिकोट बजार]`, 10 of 15). **Outside**: `क्षेत्र`, `सहर`, `जिल्ला`, `देश`, `सडक`. Where EverestNER
  is split (`बजार`, `सहर`, `प्रान्त`) the other cut is accepted.
- **Houses of parliament and the cabinet are not marked**: `संसद`, `प्रतिनिधिसभा`, `राष्ट्रिय सभा`,
  `मन्त्रिपरिषद्` (unmarked 39 of 39, 42 of 44, 295 of 304 and 32 of 32). `प्रतिनिधिसभा सदस्य` is a
  title. `सरकार` alone is not marked (777 of 872); `[नेपाल सरकार]` and `[टर्की सरकार]` are.
- **A party's short name is an organisation**: `[कांग्रेस]ले`, `[एमाले]`, `[रास्वपा]`. EverestNER
  leaves `कांग्रेस` unmarked 182 times out of 190, which the training data corrects. `माओवादी` is
  marked where it names the party and not where it means a Maoist.
- **A fiscal year is not a date**: `आर्थिक वर्ष २०८२/८३` (unmarked 13 of 14).
- **A day of the month followed by `गते` is a date**: `[१८] गते`.
- **A national side called by its country is a team, so an organisation**; the place label
  is accepted.
- **An army named by its country is marked** like `[नेपाली सेना]`: `[युक्रेनी सेना]`. Leaving it
  unmarked is accepted.
- **Names inside the name of an event, a law or a report are not marked**: the countries in
  `कोरिया-नेपाल ... प्रदर्शनी २०२६`, the year in `निवृत्तिभरण कोष ऐन २०७५`. The short name of the
  body that holds an event, where it opens the event's name (`ITU PP-26`), is accepted marked
  as an organisation or left unmarked.
- **A place inside a word for its people is marked**: `[नुवाकोट]वासी`. Leaving it is accepted.
- **A service or a product is not marked** (`स्टारलिंक`, `ग्रोक`); the company that makes it is
  (`[एक्सएआई]`).

## The labels added in 0.2

Fixed on 2026-11-13, before any text was labelled with them.

- **A value is marked without its keyword, its quotes or its brackets**, as numbers already
  are: in `password: "hunter2"` the span is `hunter2`; in `IP: 172.16.254.1/24` it is
  `172.16.254.1`, without the prefix length or a port.
- **A masked value takes the label of the whole value**: `[XXXX XXXX XXXX 4821]` is a
  `CARD_NUMBER`, `[XXXX XXXX 1234]` after "Aadhaar" a `NATIONAL_ID`.
- **`URL`** is every web address: `[https://example.com/a?b=1]`, `[www.nta.gov.np]`,
  `[moha.gov.np]`. The punctuation that ends the sentence is outside. An e-mail address is an
  `EMAIL`, also where it is used to sign in.
- **`USERNAME`** is a handle with its `@` (`[@ram_thapa]`) and a login name after its
  keyword (`username: [ram99]`). A name as it is shown on a profile (`Ram Thapa`) is a
  `PERSON`.
- **`SECRET`** is what must not be shown: a password, an API key or token, a private key
  with its BEGIN and END lines, a one-time code, a PIN, the three or four digits on the back
  of a card.
- **`CARD_NUMBER`** is the number with its spaces or hyphens. The expiry date and the name
  of the bank are not marked.
- **`ID_NUMBER`** is a number or code that an employer, a school, a hospital, an insurer, a
  seller or a maker of devices gives to one person or one device: employee code, student
  and roll number, symbol number of an examination, registration number of a person,
  customer and member number, patient and record number, policy number, IMEI, MAC address.
- **Numbers of papers and of events are not marked**: the number of a letter (`पत्र संख्या`),
  a dispatch (`चलानी नं.`), an invoice, an order, a ticket, a tender, a court case, a
  transaction reference. They name a document, not a person.
- **Codes of banks are not marked**: IFSC, SWIFT, branch and routing codes. The account
  number beside them is.
- **Short service codes are not marked**: 100, 103, 1930. A toll-free line is a phone number
  like any other and is marked.
- **Ages and amounts of money are not marked.**
- The kinds that 0.1 had are read for any country: a passport, a licence, a voter card and
  a number plate keep their label wherever they were issued.

## English and Hindi

- **Titles stay outside**, as in Nepali: `Mr.`, `Mrs.`, `Ms.`, `Dr.`, `Prof.`, `Shri`, `Smt.`,
  `श्री`, `श्रीमती`, `डॉ.`, and after the name `ji`, `जी`, `sahab`. `Jr.` is part of the name
  (`[Martin Luther King Jr.]`).
- **The possessive ending stays outside**: `[Sita]'s`. Hindi postpositions are words of their
  own and stay outside: `[मोदी] ने`, `[दिल्ली] में`.
- **An address is marked part by part**, as places in Nepali are: `[221B Baker Street],
  [London] [NW1 6XE]`. A house or flat number written with its street is inside the street's
  span, and so is a post box with its number (`[G.P.O. Box 8975], [Kathmandu]`). A postal
  code is a `LOCATION` of its own. Floor and room numbers alone are not marked.
- **Words for a people or a language are not places**: `Nepali`, `Indian`, `American`,
  `नेपाली`, `भारतीय`. `the US` and `U.K.` are.
- **A year is a date where the text uses it as one**: `in [2019]`, `since [1994]`,
  `[January 2024]`, `[March 5]`. A month alone, a weekday, a decade (`the 1990s`), a time of
  day, a duration and an age are not dates, as in Nepali.
- **Newspapers, channels and sites that act are organisations**: `[Reuters] reported`,
  `according to [The Kathmandu Post]`. A product or a service is not marked (`WhatsApp`,
  `Excel`); the company that makes it is (`[Microsoft]`).

## Settled while labelling the sets of 0.2

These came up in `real-news-v2`, `real-en-v0` and `real-hi-v0` (2026-11-13): the two passes
differed there, or both noted that the guide did not decide.

- **The end of a month is a date**: `[असोज मसान्त]`, as `real-gov-v0` has it. A week of a month
  (`असोज दोस्रो साता`) is not.
- **A year of any era is a date, with the word for its era**: `[Nepal Sambat 1147]`. The name of
  an era alone is not marked, and a lunar day (`Kartik Shukla Chaturthi`) is not a date.
- **A direction word before a region is outside**: `southeastern [Europe]`. It is inside where
  it is part of the name: `[दक्षिण कोरिया]`, `[South Africa]`. `real-news-v1` has
  `[दक्षिणपूर्वी युरोप]`; both cuts are accepted.
- **In Hindi `साल` stands before the year** and is inside like the Nepali `साल` after it:
  `[साल 1983]`. The year alone is accepted.
- **The maker's name inside the name of a product is not marked**: `Maruti Suzuki 800`. Marking
  it is accepted.
- **A deity is not a person.**
- **`पुल`, `घाट` and `Ghat` are type words that belong to the name of a place.**

## Text of web pages

Settled on 2026-11-13 while `real-web-v0` and `real-enweb-v0` were labelled: pieces of pages
of schools, hospitals, cooperatives, associations and news rooms, about 300 characters each,
with menus, lists of staff, contact blocks and footers. Where a second reading is named as
accepted, the scorer takes either.

- **A menu word, a heading or the name of a section is not marked**, also when it is the
  name of a place (`हङकङ` as a section of a news site), and the name of the outlet inside the
  name of one of its sections or products is not marked either. A place marked there is
  accepted.
- **A job title, a role or a degree beside a name is not part of it.**
- **A name that the edge of a piece cuts is not marked.** Where what is left reads as a
  whole name, marking it is accepted.
- **A unit with its parent is one span**, the comma inside:
  `[नेपाल पत्रकार महासंघ, केन्द्रीय समिति]`. The parent alone is accepted.
- **A branch, a counter or an office named by its place is an organisation**:
  `[Thamel Branch]`, `[मालपोत कार्यालय, खाँदवारी]`. The place alone as a `LOCATION` is accepted.
  A table cell that holds only the name of the place is a `LOCATION`.
- **An inner body of the organisation whose page it is** (a department, a commission, an
  assembly) is not marked. Marked is accepted where it has a name of its own.
- **A school, a club or a hospital with a name of its own, and the place where it stands,
  are two spans**: `[जनता माध्यमिक विद्यालय] [धरान]`. One span is accepted.
- **`श्री` or `Shree` before the name of an institution stays outside**, as before a person.
  Inside is accepted.
- **The type word of a street in an address is inside**: `[कुपण्डोल रोड]`, as `[लेखनाथ मार्ग]`
  and `[221B Baker Street]`. The name alone is accepted.
- **`Mount` or `Mountain` before a peak is inside.** The name alone is accepted.
- **A fund that is set up as a body is an organisation.**
- **A phone number ends before a slash that adds the endings of further numbers**
  (`[01-4412345]/46/47`). The whole is accepted. A plus sign written before the number is
  part of it. An extension is outside.
- **A code of a map** (a Google plus code) **is a `LOCATION`**, like a postal code.
- **The year in a copyright line is a date. A range of years that names a term in a list of
  options (`2025-2027`) is not marked**, like a fiscal year. Each year as a date is accepted.
- **What a site shows in place of a hidden address** (`[email protected]`) **is not an
  address** and is not marked. An address that a page shows without its signs
  (`info example edu np`) is an `EMAIL`; unmarked is accepted.
- **A list of bare years to choose from** (an archive by year) **is not marked.** Each year
  as a date is accepted.
- **A second family name in brackets after a name** (`Sita Thapa (Gurung)`) **is a span of
  its own.** One span with the brackets inside is accepted.
- **The registration number of an organisation is not marked**, also where a page puts it
  after the keyword of a tax number. A tax number of an organisation is a `TAX_ID`.
- **A year that closes the title of a notice, a report or a set of photographs is not
  marked**, like the year in the name of a law (`... सम्बन्धि सुचना २०८२`). The year as a date
  is accepted. Settled on `real-gov-v1`, where the two passes differed in 2 of 71 texts.

## Romanised Nepali and mixed text

- The same rules hold. **A case marker is outside whether it is written attached or apart**:
  `[Ram]le`, `[Kathmandu] ma`, `[Pokhara]ko`, `[Sita] lai`.
- **Words of kinship and respect stay outside**: `dai`, `didi`, `bhai`, `bahini`, `sir`,
  `madam`, `ji`, `jyu`, `guru`.
- **A name is marked however it is spelled or cased**: `[balen]`, `[KTM]`, `[ktm]`.
- A handle is a `USERNAME` and not a `PERSON`, also when it is built from a name
  (`[@balen]`). A name with no `@` that addresses someone in a comment is a `PERSON`.

