# Annotation guide

These rules decide where a span starts and ends and which label it gets. They follow
EverestNER wherever it has a clear habit, so that its labels and ours can be trained
together. The counts below are from the EverestNER training file.

The rules were written for Nepali. Release 0.2 adds seven labels and English, Hindi and
romanised Nepali; what that changes is in the last three sections. A rule stated for Nepali
holds for the other languages unless one of those sections says otherwise.

## Labels

The one set of 1.0, shared by the model, every training text, every test set and the
dataset of practical paragraphs (fixed on 2026-11-17). The last column gives
the name a label had in releases 0.1 to 0.3 and in the batches of the dataset; files and
models that use an older name are read under the final one. The section "The labels of 1.0"
at the end says what the new labels cover.

| Label | Covers | Older names |
|---|---|---|
| `PERSON` | Names of people: full, given only, family only, initials with a family name | |
| `LOCATION` | Named places: countries, provinces, districts, local levels, toles, streets, chowks, airports | |
| `ORGANIZATION` | Named organisations: banks, offices, companies, schools, hospitals, parties | |
| `DATE` | A calendar day, month or year in Bikram Sambat or the Common Era that is not a date of birth | |
| `ADDRESS` | Where a person lives, owns land or receives deliveries, written out as an address: one span | marked place by place as `LOCATION` before 1.0 |
| `DOB` | A date of birth | `DATE` before 1.0 |
| `PHONE` | Mobile and landline numbers | |
| `EMAIL` | E-mail addresses | |
| `URL` | Web addresses, with or without `http` | |
| `DIGITAL_SECRET` | Handles and login names; IPv4 and IPv6 addresses; the IMEI, MAC or serial of a device; passwords, keys, tokens, one-time codes, PINs | `USERNAME`, `IP_ADDRESS`, `SECRET`, `DEVICE_ID` |
| `NATIONAL_ID` | A number by which a state knows a person: citizenship certificate, Nepal's NIN, Aadhaar, a social security or national insurance number, a resident identity number | `CITIZENSHIP_NO`, `AADHAAR`, `CITIZENSHIP_ID` |
| `TAX_ID` | Tax number: PAN and VAT in Nepal (one number), PAN and GSTIN in India, EIN and TIN | `PAN` in release 0.1 |
| `PASSPORT` | Passport number | `PASSPORT_NO` |
| `DRIVER_LICENSE` | Driving licence number | `LICENSE_NO`, `DRIVING_LICENSE` |
| `VOTER_ID` | Voter identity number | |
| `MEDICAL_ID` | A number that a hospital, a health service or a health insurer gives to a patient or member | `ID_NUMBER` before 1.0, `HEALTH_ID` |
| `EMPLOYEE_STUDENT_ID` | A number that an employer, a school, an examination board or a provident, pension or social security fund gives to its worker, student or member | `ID_NUMBER` before 1.0 |
| `PROPERTY_UTILITY_ID` | The number of a plot of land or of a service to a household: plot, sheet, ration card, consumer and meter numbers | `ID_NUMBER` before 1.0 |
| `ID_NUMBER` | Any other number that names one person: a council or bar registration, a policy that is not health insurance, a membership, a customer number, a visa | |
| `BANK_ACCOUNT` | Bank account number, IBAN, DEMAT number | |
| `CREDIT_CARD` | Payment card number, credit or debit | `CARD_NUMBER`, `PAYMENT_CARD` |
| `PAYMENT_ID` | A handle or identity through which money is sent to a person: a UPI address, a wallet identity | `UPI_ID` |
| `VEHICLE_ID` | Vehicle registration number, chassis number | `VEHICLE_PLATE` |

`LOCATION`, `ORGANIZATION`, `DATE` and `URL` are names of things. The other nineteen are
personal data: what the profile `personal` of the runtime takes out of a text.

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
- A range of days gives two dates, and the bare day that closes it is one of them:
  `[माघ ५] देखि [७] सम्म`, `[July 3] to [26]`, `[September 8]-[9]` (14 of 14 in the sets
  labelled by hand).
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

- **A span does not run over a line break.** Each line of a page is a block of its own: a
  cell, an entry of a list, a line of an address. A name that a page prints on two lines
  (the given name on one, the family name on the next) is two spans, and the labels of the
  test sets are written that way.
- **A menu word, a heading or the name of a section is not marked**, also when it is the
  name of a place (`हङकङ` as a section of a news site), and the name of the outlet inside the
  name of one of its sections or products is not marked either. A place marked there is
  accepted, and so is the outlet in a heading that only adds a word for what follows
  (`... Team` above its staff, `... नीति` above its policies), as `real-web-v0` and
  `real-web-v1` hold it.
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

## Settled while labelling web pages for training

These came up on 2026-11-14 in pieces of web pages that were labelled for training, where
the first readers noted that the guide did not decide. Each follows what the test sets
already have, or the nearest rule above.

- **A fax number is a `PHONE`**, as `real-enweb-v0` and `real-gov-v1` have it.
- **A building with a name in an address is a `LOCATION` of its own, with its type word**:
  `[Sunrise Complex], [New Road], [Kathmandu]`, as in `real-web-v0` and `real-enweb-v0`.
  A floor or a room number is not marked. A building that is named as a body
  (`[Chamber Bhawan]` as the seat that acts) is an `ORGANIZATION`.
- **A list of places to choose from** (the options of a filter or of a form field:
  districts, provinces, countries) **is not marked**, like a list of bare years and like a
  menu. Each place as a `LOCATION` is accepted.
- **A list of links to other bodies names them**: each is an `ORGANIZATION`
  (`[Nepal Rastra Bank]`, `[Ministry of Health and Population]`). The site's own sections in
  a menu are not marked.
- **A name at the edge of a piece that reads as a whole name is marked.** One that is cut
  for all to see (it ends on a title, on a middle name or inside a word) is not.
- **The registration number that a council gives to one doctor, nurse or engineer is an
  `ID_NUMBER`**, as a registration number of a person. The number under which an
  organisation is registered is not marked.
- **A year that heads an entry of a timeline is a date**, and so is the caption of a
  calendar (`[November 2026]`). The days of the calendar are not.
- **A number that a page shows as an example or a placeholder is marked like a real one**
  (`[98XXXXXXXX]`, `[9800000000]`): the label says what kind of value stands there.
- **A country or an area code in brackets is part of the phone number**, with its brackets:
  `[(+977) 1-4412345]`, `[(061) 520123]`, as `real-enweb-v0` has it. A list of country
  codes to choose from is not marked.
- **The registration mark of an aircraft** (`9N-ABC`) **is not marked.** `VEHICLE_PLATE` is the
  number plate of a road vehicle.
- **The name of a bank in the details of an account is an `ORGANIZATION`** like any other
  body (`[Nabil Bank Ltd.]`, `A/C No. [0123456789]`), as `real-gov-v0` has it, and so is the
  holder of the account where it is a body. The rule under `CARD_NUMBER` only keeps the name
  of the bank out of the span of the number.
- **The full name of a person is marked wherever it stands**, also as an item of a menu or
  as the name of a section (a page about the founder, about the person a centre is named
  after). A name alone on a line looks the same in a list of staff, and a detector is there
  to find it. The name of a person inside the name of a body, a prize or a road stays a part
  of that name.
- **A newspaper, a weekly, a magazine, a radio or a television station is an `ORGANIZATION`
  with its type word** (`[कान्तिपुर दैनिक]`, `[युगबोध साप्ताहिक]`), also in a list of what a body
  publishes. The title of one book, one report or one issue of a bulletin is not marked.
- **The department in the registration line of a news site is an `ORGANIZATION`**
  (`[सूचना तथा प्रसारण विभाग] दर्ता नं. ...`): there is only one of it. The number is the
  registration number of an organisation and is not marked.
- **A web address that the page itself shortens is a `URL` as far as it is shown**, without
  the dots that end it (`[www.example.org.np/notice/20]...`).
- **A line of rights is a copyright line** also without the sign (`सर्वाधिकार सुरक्षित २०८२`):
  its year is a date, and a year given in two eras with a slash is two dates.
- **A local level or an office before the title of its own law, plan, budget or profile is
  marked as the body that makes it**: `[बनेपा नगरपालिका]को आर्थिक ऐन, २०८०`, as `real-gov-v0` and
  `real-gov-v1` have it (15 of 15). The year of the law is not marked. As a place is accepted.
- **A road, a bridge, a canal or a water scheme named by the places it joins or serves**
  (`[चरिकोट]-[जिरी] सडक`, in the title of a work or of a call for bids) **gives a `LOCATION` for
  each place, the type word outside**, as places joined by a hyphen are marked one by one.
  A street of an address keeps its type word (`[कुपण्डोल रोड]`). A gate, a park or a hall
  named after a person is one `LOCATION`, the name of the person a part of it.
- **A ministry with its portfolio is a name, also the ministry of a province**
  (`[सामाजिक विकास मन्त्रालय]`): the portfolio tells which one, as in `[गृह मन्त्रालय]`. **A body
  named only by its level** (`प्रदेश लोक सेवा आयोग`, `प्रदेश लेखा नियन्त्रक कार्यालय`, `जिल्ला अदालत`)
  **is a kind of body and is not marked** until the place stands with it
  (`[कोशी प्रदेश लोक सेवा आयोग]`, `[जिल्ला अदालत काठमाडौं]`). So the readers of the government
  pages and of the news had it; marked is accepted where the text makes plain which one.
- **A ministry of a province followed by its province is one span**, the comma or the
  hyphen inside (`[सामाजिक विकास मन्त्रालय, कोशी प्रदेश]`), as a unit with its parent and as an
  office named by its place: the province tells it from the ministry of the federation
  with the same portfolio. The town after them is a place of its own. The ministry and the
  province apart is accepted. Settled on `real-gov-v2`, where the two passes differed in 3
  of 61 texts.
- **A year that names a batch, an intake, an academic session or an edition is not marked**
  (`Batch 2075`, `Intake 2026`, `शैक्षिक सत्र २०८२`), like a fiscal year and like a range of
  years that names a term: it names a group or a stretch of time, not the day something
  happened. The year as a date is accepted.
- **A branch or an office named by its place is marked where the page lists it as a body**
  (a list of branches, a contact block, a table: `[Thamel Branch]`), **and not where it is
  an entry of the menu of its own site**, which is a menu word that leads to a section.
  Where a piece does not show which of the two a list is, it is marked, as `real-enweb-v1`
  has it.

## Romanised Nepali and mixed text

- The same rules hold. **A case marker is outside whether it is written attached or apart**:
  `[Ram]le`, `[Kathmandu] ma`, `[Pokhara]ko`, `[Sita] lai`.
- **Words of kinship and respect stay outside**: `dai`, `didi`, `bhai`, `bahini`, `sir`,
  `madam`, `ji`, `jyu`, `guru`.
- **A name is marked however it is spelled or cased**: `[balen]`, `[KTM]`, `[ktm]`.
- A handle is a `USERNAME` and not a `PERSON`, also when it is built from a name
  (`[@balen]`). A name with no `@` that addresses someone in a comment is a `PERSON`.

## Settled while labelling romanised comments

The first three came up in `real-roman-v0` (2026-11-13), where the two passes differed in
four comments. The rest came up on 2026-11-14 in comments that were labelled for training,
where the first readers noted that the guide did not decide.

- **A stage name or an alias that one person goes by is a `PERSON`**: the name of a rapper,
  the alias of a video maker, the character a comedian is known as. A title that is part of
  a stage name is inside; outside is accepted.
- **A pet name or a nickname that is used to call one person is a name.** Unmarked is
  accepted where it may be a plain endearment. **An epithet or a description is not a name**
  (`the man from Nuwakot`, a word of abuse); marked is accepted where it may be a nickname.
- **A line that stands for a song, a film or a show is not marked**, nor is a name inside it.
- **A party called by its election symbol** (`surya`, `ghanti`) **is not marked**: the symbol
  is no word of its name. Its name and its short name are marked (`[emale]`, `[rsp]`).
- **A channel, a page, a band, a club or a fan group with a name of its own is an
  `ORGANIZATION`.** In `[Samrat] ko vlog`, said of the videos a person makes, the name is a
  `PERSON`.
- **A shop, an eatery or a hotel with a name is an `ORGANIZATION`.** A ground, a hall or a
  park is a `LOCATION`, as a stadium is.
- **A character of a film or a show is a `PERSON`.** A deity or a venerated figure of a
  religion is not; a living preacher is.
- **The number of a constituency stays outside**, like a ward number: `[Jhapa] 5`.
- **A name inside a hashtag is marked without the `#`**, also where the tag joins it to other
  words (`#[balen]`, `#[balen]forpm`). Leaving a joined tag unmarked is accepted.
- **After an `@`, one token is a `USERNAME` with its `@`** (`[@ram_thapa-x1y]`). A display name
  written with spaces after an `@` is a `PERSON` without it (`@[Ram Thapa]`).
- **A word for the people of a place is not marked** (`jhapali`, `pokhreli`), as `nepali` is
  not. A place inside a compound for its residents is (`[nuwakot]basi`), as in Devanagari.

## Settled while labelling the test sets of the next version

These came up on 2026-11-14 where the two passes over `real-news-v3`, `real-en-v1`,
`real-enweb-v1` and `real-hi-v1` differed. The other reading is accepted in each.

- **The name of an exchange before the word for its index is not marked**
  (`नेप्से परिसूचक`, `NEPSE index`): it names the index, like the maker's name inside the name
  of a product. EverestNER leaves it in 7 of 8 cases and DanfeNER in 3 of 3. The exchange
  where it acts is an `ORGANIZATION` (`[नेप्से]मा सूचीकृत`).
- **A mutual fund under which schemes run is an `ORGANIZATION`**, as a fund that is set up
  as a body. The scheme whose units are sold is a product and is not marked.
- **A short form in quotes after an organisation is cut like one in brackets**: one span
  with the quotes inside, two spans accepted.
- **A kind of office with its place after a preposition** (`the District Police Office in
  [Dolakha]`) **gives the place alone**: the place is no part of a name there. With the place
  inside the name it is one span (`[District Police Office, Dolakha]`).
- **A code in brackets after a branch or an office is not a short form** (`[Thamel Branch]
  (THM)`): it is a code and not a name the branch is called by, so it stays outside and is
  not marked.
- **A number that the edge of a piece cuts is treated like a name that it cuts**: a phone
  number that lost its area code is like a family name whose given name is gone. In a test
  set what the edge cuts is not marked, and marking what is left is accepted where it reads
  as whole. In text labelled for training what reads as whole is marked, as said under the
  web pages for training: a detector that meets it cannot know that something is missing.
- **In Hindi the word for a block or a tehsil stays outside**, like the word for a district:
  `[मोहनलालगंज] ब्लॉक`, `[सदर] तहसील`. HiNER cuts `तहसील` off in 1,705 of 1,762 cases.

## Settled while labelling Hindi for training

These came up on 2026-11-14 in 300 rows of Hindi that were labelled for training
(`gold-hi-01`, `gold-hi-02`), where the first readers noted that the guide did not decide.
Each follows the nearest rule above; `real-hi-v0` has the first six the same way.

- **Type words of places.** Inside the name: `गांव` after the name of a village, `नदी`, `रोड`,
  `हाईवे`, `चौराहा`, `तिराहा`, `मोहल्ला`, `रेलवे स्टेशन`, `बस पड़ाव`, `छावनी`, `धाम`, also in an inflected
  form (`[हजरतगंज चौराहे] पर`). Outside: `जिला`, `ब्लॉक`, `तहसील`, `थाना क्षेत्र`, and a word for a
  village or a local body that stands before the name (`ग्राम [रामपुर]`, `गांव [रामपुर]`,
  `ग्राम पंचायत [रामपुर]`).
- **`वर्ष` before a year is inside the date**, like `साल`: `[वर्ष 2014]`. A year with a
  genitive before what happened in it is a date (`[2014] के चुनाव`).
- **A body named only by its level or its kind is not marked**: `केंद्र सरकार`, `राज्य सरकार`,
  `राज्य निर्वाचन आयोग`, `केंद्रीय बैंक`, `हाईकोर्ट`, `नगर पालिका`, `थाना पुलिस`. With the word that
  tells which one it is a name: `[महाराष्ट्र सरकार]`, `[चुनाव आयोग]`, `[बॉम्बे हाईकोर्ट]`.
- **A department with its field is a name**, like a ministry with its portfolio:
  `[वन विभाग]`, `[राजस्व विभाग]`.
- **An alliance of parties that goes by a name is an `ORGANIZATION`**, the word for the
  alliance inside where it is part of the name: `[एनडीए]`, `[इंडिया गठबंधन]`, `[महागठबंधन]`.
  `गठबंधन` alone is not marked.
- **The party or the person before `सरकार` is marked and `सरकार` stays outside**:
  `[कांग्रेस] सरकार`, `[गहलोत] सरकार`. So does the word for a family after a name
  (`[मुलायम] परिवार`).
- **The body before the word for its election is marked**: `[गुजरात विधानसभा] चुनाव`. A house of
  parliament stays unmarked there as elsewhere (`लोकसभा चुनाव`).
- **A national side named with the adjective of its country and a word for the side is an
  `ORGANIZATION`**, like an army named by its country: `[भारतीय महिला क्रिकेट टीम]`,
  `[भारतीय टीम]`. `[टीम इंडिया]` is marked whole. After the name of the country `टीम` is
  outside (`[भारत ए] टीम`).
- **A police station or an outpost named by its place is an `ORGANIZATION`**, also in an
  inflected form (`[कल्याणपुर थाने] में`).
- **Two names joined by `उर्फ` are two `PERSON` spans.**
- **The name of a body given again in full in another language in brackets is a span of
  its own.** A short form in brackets stays inside the span.
- **A train or a bus service is a service and is not marked** (`राजधानी एक्सप्रेस`). A word
  for a member of a party is not marked (`कांग्रेसी`).

## Settled while labelling Nepali news for training

These came up on 2026-11-15 in the last part of Nepali news that was labelled for training
(`gold-news-ne-05`). The first reader noted them and the second left them standing.

- **A type word in neither list is inside where the two words are the name of the thing**:
  a border point, a square, a road (`[काँकरभिट्टा नाका]`, `[वसन्तपुर डबली]`, `कोरिडोर` after the
  places a road joins). It is outside where it only says what lies at the place
  (`[गोरुसिङ्गे] जंगल`).
- **The building of a body is a `LOCATION` where the row names the building**, also where
  the body itself is not marked: `[सङ्घीय संसद् भवन]`.
- **A short form of the given name in brackets between the given name and the family name
  is inside the one `PERSON` span.**

## The labels of 1.0

Fixed on 2026-11-17, when the dataset of practical paragraphs joined the real text. The
rules for the address and the date of birth are those under which the second batch of that
dataset was written; the first batch follows them in what was read of it.

- **An `ADDRESS` is where a person lives, owns land or receives deliveries, written out.**
  It needs at least one part below the city: a house or flat number, a street, a tole or
  locality, a ward, a village, a postal code. The whole address is one span, with its city,
  district, state, postal code and country where they are written as part of it:
  `[धरान उपमहानगरपालिका वडा नं. १५, बाझोगरा मार्ग, घर नं. २१४]`,
  `[742 Maplewood Terrace, Brookline, MA 02445]`. A word that only names the kind of thing
  before it (`ठेगाना:`, `residing at`) is outside.
- **A city, a district, a state or a country on its own is not an `ADDRESS`.** It is a
  `LOCATION`, as before.
- **The address of an office, a branch, a hospital, a school, a court or a shop is not an
  `ADDRESS`.** Its places are `LOCATION`s one by one, as the web pages have them. It becomes
  an `ADDRESS` only where a person gives it as the place to deliver to them.
- **In text labelled before 1.0 the place where someone lives stands as `LOCATION`s**
  (`[धरान]-१५ बस्ने`), and a date of birth as a `DATE`. The test sets keep those labels, and a
  score on them counts an `ADDRESS` with the places and a `DOB` with the dates. A model of
  1.0 learns the address as one span from the practical paragraphs.
- **A `DOB` is a date of birth with at least two of day, month and year**; a birthday given
  as month and day counts. An age, a year alone, and every other date of a person's life
  (issue, visit, payment, joining, death) are not a `DOB`.
- **`DIGITAL_SECRET` holds what three labels held**: a handle with its `@` and a login name
  after its keyword; an address of a machine without prefix length or port; the IMEI, MAC
  or serial of a person's device; a password, key, token, one-time code or PIN. A link to a
  person's own profile is a `DIGITAL_SECRET` in the practical paragraphs; any other web
  address is a `URL`.
- **`PAYMENT_ID` is a handle or identity through which money reaches a person**: a UPI
  address, an eSewa, Khalti or Paytm identity, a PayPal or Venmo handle. An account number
  is a `BANK_ACCOUNT`, a card number a `CREDIT_CARD`.
- **Which number is whose kind.** `MEDICAL_ID`: patient and record numbers, a health
  insurance policy or member number, an employees' state insurance number.
  `EMPLOYEE_STUDENT_ID`: employee, staff, payroll and badge numbers; UAN, PF, PPO and
  pension numbers; the contributor numbers of the provident fund, the Citizen Investment
  Trust and the Social Security Fund; a labour permit; student, roll, symbol, examination,
  admission and university registration numbers. `PROPERTY_UTILITY_ID`: plot, sheet, kitta
  and khasra numbers; a ration card; the consumer, connection or meter number of
  electricity, water, gas, telephone or internet. `NATIONAL_ID` also takes an alien
  registration number and a resident identity number. `ID_NUMBER` is every other number
  that names one person: the registration that a council, a bar or a board gives to one
  doctor, engineer, advocate or teacher; a life, vehicle or travel policy; membership,
  loyalty and customer numbers; a visa or a residence permit; birth registration; a
  disability card; shareholder and folio numbers.
- **`VEHICLE_ID`**: the plate of a vehicle with a named owner or driver, and a chassis
  number. In the practical paragraphs the plate of a bus, an ambulance or a rental car is
  left alone.
- **Whose a phone number and a mailbox are** (settled on 2026-11-17). Every
  phone number and every e-mail address is marked, as before: `PHONE`, `EMAIL`. Where
  every label is asked for, that is all. The profile `personal` leaves alone the number of
  an office, a helpline, a reception or a toll-free line and a shared mailbox (`info@`,
  `support@`, `hr@`): they are no person's. A text labelled before 1.0 does not say which
  is which; the practical paragraphs do, and a model of 1.0 learns it from them.
- **A number that is already masked** (`XXXX XXXX 4521`, `98******12`, `ra****@...`) is
  marked under the label of the whole number where every label is asked for, as before, and
  left alone under `personal`. This holds in every batch of the practical paragraphs, also
  where a batch has such a number among its answers.
- **The name of a god, of a figure of history or of fiction, and the name of a speaker at a
  public event** are strings that the practical paragraphs leave alone. Real text labelled
  here marks the name of every person. A model is taught the first as nothing in the
  practical paragraphs and is not taught on the name of a speaker.
- **A private body** (the employer or the school of one person) is an `ORGANIZATION`, a
  thing: `personal` does not take it out. Batch 3 marks 92 of them; they stay marked as
  organisations and are not counted under `personal`.
- **The practical paragraphs are held to this guide** (2026-11-18). Their three batches were
  written at different times, and where a batch has an answer other than the guide, the
  guide stands: `गते` is outside a date of birth and the extension is outside a phone number,
  as in the real text.
- **The number of a paper or an event stays unmarked in the practical paragraphs too**, as
  the rule of 0.2 has it: the reference of a booking, a ticket, an order, a complaint, a
  police report or a court case, an application, a loan, a receipt, one payment or
  transaction, the dispatch number of a letter. It names the paper, not the person, also
  where the paper is one person's own. Batch 3 has such references among its answers; they
  are strings to leave alone. A second reader told them apart from the numbers that name a
  person.
- **What that reader settled at the edge of the two.** A number under which a hospital or a
  laboratory keeps one patient's file, sample or stay is a `MEDICAL_ID` (admission, OPD,
  specimen and prescription numbers), and so is the number of a health insurance claim.
  The plot of a private person's land is a `PROPERTY_UTILITY_ID` wherever it is named, also
  the neighbour's and the co-heir's. A registration of birth, marriage or death, the code
  under which a study knows one participant, the chip or tag of a person's animal, and the
  registration that a council gives one doctor or nurse are `ID_NUMBER`s. A loyalty or
  frequent flyer account is an `ID_NUMBER`, not a `PAYMENT_ID`; a wallet identity or wallet
  address is a `PAYMENT_ID`, also of a crypto wallet. The code of a bank or a branch, the
  number of a company, of a law, of a flight is nobody's.
