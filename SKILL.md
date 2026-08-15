# OmniPort Framework — SKILL.md

Questo documento istruisce qualunque LLM (agente app-builder o assistente per lo sviluppo del framework stesso) su come scrivere codice per OmniPort in modo sicuro, verificabile e coerente con le convenzioni del progetto. È la fonte di verità: in caso di dubbio, questo file vince su intuizioni generiche di "buon senso" da altri progetti.

---

## 🏗️ Principi Architetturali

OmniPort segue una **Hexagonal Architecture** (Ports & Adapters): la logica di business è isolata dall'infrastruttura, secondo il pattern **MVA — Model / View / Action** (evoluzione dell'MVC dove le Action sostituiscono i controller come unità indipendenti e caricate dinamicamente).

1. **Core (`src/application/`)**: logica di dominio pura, definizioni UI, modelli dati. Zona di modifica primaria.
2. **Infrastructure (`src/infrastructure/`)**: implementazioni concrete (adapter web, persistenza, sensori, autenticazione...). Modificabile solo per aggiungere/correggere un adapter specifico, mai per cambiare il contratto della Port che implementa.
3. **Framework (`src/framework/`)**: il kernel — loader, container DI, manager. Modificabile **solo** in "Framework Maintenance Mode" (vedi sotto), mai in modalità app-building.

---

## 🛑 Regole di Scope — due modalità operative

Non tutti gli agenti che leggono questo file hanno lo stesso livello di fiducia. Prima di scrivere una riga di codice, stabilisci in quale modalità stai operando.

### Modalità 1 — App Builder (default, per chi costruisce/modifica un'app sopra il framework)
Sei **autorizzato SOLO** a:
1. Creare o modificare file dentro `src/application/` e sue sottocartelle.
2. Modificare `pyproject.toml` per configurare il progetto o attivare/disattivare adapter.

Sei **vietato** a toccare `src/framework/` o `src/infrastructure/` in questa modalità, anche se pensi di aver trovato un bug lì — segnalalo, non correggerlo.

### Modalità 2 — Framework Maintenance (solo su autorizzazione esplicita dell'umano, per file specifici)
Attivabile **solo** quando l'umano indica esplicitamente quale file di `src/framework/` o `src/infrastructure/` sei autorizzato a modificare (es. "lavora solo su `src/framework/manager/tester.py`"). In questa modalità:
- Lavori su **un solo file/manager per volta**. Non toccare altri componenti "già che ci sei", nemmeno per fix banali — segnalali e basta.
- Segui obbligatoriamente la **Disciplina Test-First e Contract** descritta sotto.
- Non hai comunque il permesso di introdurre nuovi pattern architetturali (nuove classi base, nuovi meccanismi di DI, ecc.) senza che sia l'umano a richiederlo esplicitamente.

---

## 🧪 Disciplina Test-First e Contract (obbligatoria in Modalità 2, consigliata sempre)

Il framework ha già il meccanismo per impedire che codice non verificato arrivi in produzione: **usalo, non aggirarlo.**

1. **Prima di modificare un manager/componente, scrivi o aggiorna il suo `*.test.dsl`** nella stessa cartella (es. `src/framework/manager/tester.test.dsl` per `tester.py`). Il test è la specifica: se non riesci a scrivere un test per il comportamento che stai per aggiungere, non hai ancora capito bene cosa deve fare.
2. **Implementa il fix/feature.**
3. **Verifica con il filtro dedicato**, non con l'intera suite:
   ```bash
   python3 public/main.py --test managers/<nome_manager>
   ```
   (filtri disponibili: `managers`, `ports`, `services`, `infrastructure`, oppure un path diretto)
4. Se il test passa, `Contract.record_tested` aggiorna l'hash nel contract JSON accanto al file — è quello che permette il boot in modalità strict.
5. **Non usare mai `--skip-verify` come soluzione a un test che fallisce.** È un flag di emergenza per l'umano, non un modo per far "sparire" un errore che hai introdotto. Se un test fallisce dopo una tua modifica, il problema è nella modifica, non nel test.
6. **Un manager modificato = un commit = un contract aggiornato.** Non accumulare modifiche a più componenti in un solo commit: rende impossibile capire quale hash corrisponde a quale comportamento verificato.

---

## 🚫 Anti-pattern vietati

Questi pattern sono stati trovati nel codice esistente durante una review e sono **esplicitamente vietati** da qui in avanti. Se li incontri in un file che stai già autorizzato a toccare, correggili; se li incontri altrove, segnalali senza correggerli (rispetta lo scope).

1. **Metodi "versione 2"** (`post2`, `install2`, `foo_v2`...): mai lasciare una seconda versione di un metodo accanto all'originale. O sostituisci l'originale con la logica corretta, o elimini la versione superata. Un metodo `_2` permanente è debito tecnico, non un'opzione valida.
2. **Init fantasma:** mai scrivere logica di inizializzazione reale dentro una stringa triple-quote (`'''...'''`) lasciata inerte in `__init__` o altrove. O il codice viene eseguito per davvero (assegnazioni dirette su `self.`), o va rimosso. Prima di consegnare un file, verifica che ogni `self.<attributo>` usato altrove nella classe sia effettivamente assegnato in un punto del codice che viene eseguito.
3. **Naming misto italiano/inglese negli identificatori:** i nomi di classi, metodi, funzioni e variabili sono **sempre in inglese**. L'italiano è benvenuto in commenti, docstring e messaggi di log/errore mostrati all'utente, mai negli identificatori di codice.
4. **Sinonimi CRUD non decisi:** per operazioni di persistenza usa sempre `create` / `read` / `update` / `delete` come verbi di base. Se un'operazione ha davvero una semantica diversa da un CRUD standard (es. un riepilogo leggero vs una lettura completa), dalle un nome esplicito che comunichi la differenza (es. `summary()` vs `read()`), non un sinonimo generico lasciato ambiguo.
5. **Prefissi incoerenti su un gruppo di metodi legati alla stessa risorsa:** se un manager gestisce il ciclo di vita di una sessione, tutti i metodi relativi condividono lo stesso prefisso — `session_create`, `session_get`, `session_activate`, `session_terminate`, `session_reinstate` — non un mix di nomi con e senza prefisso.
6. **Verbi generici senza contesto** (`resolve`, `compute`, `check`, `process`): il nome del metodo deve dire cosa risolve/calcola/controlla. Preferisci `resolve_route()` a `resolve()`, `validate_components()` a `check()`.
7. **Debug lasciato nel codice di produzione:** niente `raise Exception(f"[debug] ...")`, `print()` di debug commentati a metà, o branch morti lasciati "per sicurezza". Se serve loggare, usa `framework.service.diagnostic`.

---

## 🔁 Metodo operativo di sviluppo (per sessioni di lavoro con un LLM)

1. **Un solo target per sessione.** Un manager, un adapter, una action — mai "sistema un po' di cose sparse".
2. **Contesto minimo e mirato:** fornisci all'LLM solo il file target, il suo `*.test.dsl` (se esiste) e i moduli da cui dipende direttamente (import diretti). Non l'intero repo.
3. **Se esiste un contract JSON accanto al file**, forniscilo come contesto: mostra all'LLM quali componenti sono già certificati, così non li tocca per sbaglio mentre lavora sul resto.
4. **Passata separate per tipo di modifica:** bugfix, rename/refactor e nuova feature sono tre passate diverse, non un unico prompt onnicomprensivo. Diff piccoli e a scopo singolo sono più facili da revisionare e da far passare nel gate dei test.
5. **Ordine di priorità consigliato quando più componenti hanno problemi:** prima i bug che rompono l'esecuzione (AttributeError, import mancanti, metodi che referenziano attributi mai inizializzati), poi la disciplina test-first mancante, poi rename/naming, infine nuove feature.

---

## 📁 Struttura Directory (`src/application/`)

- `action/`: logica di dominio in `.dsl` (o `.py` per casi non esprimibili nel DSL).
- `model/`: entità e schemi in `.json`.
- `repository/`: pattern di accesso ai dati.
- `view/`: definizioni UI in `.xml`.
  - `page/`: pagine applicative principali.
  - `layout/`: layout condivisi.
  - `component/`: componenti riutilizzabili.
- `policy/`: regole di sicurezza e business (`.toml`).
- `locales/`: file di traduzione/i18n.

---

## ✍️ DSL (Domain Specific Language)

Prima di creare o modificare business logic in un file `.dsl`, leggi sempre `src/application/dsl.md` per la sintassi completa e le funzioni built-in disponibili.

**Costrutti principali:**
- Assegnazione: `var_name := value;`
- Pipe: `input |> function1(args) |> function2;`
- Task/trigger: `trigger(kwargs) -> action_or_pipe;`
- Trigger schedulati: `tick(schedule: 5) -> azione;`
- Schemi tipizzati:
  ```
  type:user_schema := {
      "name": { "type": "string", "required": true };
      "age":  { "type": "integer", "default": 18 };
  };
  ```

**Vincoli sintattici stretti:**
- Niente virgole finali in dizionari `{}` o liste/tuple `()`, `[]`.
- Commenti su singola riga con `//`. I blocchi `/* ... */` non si annidano: il primo `*/` incontrato chiude il blocco, indipendentemente dall'intenzione.

---

## 🖼️ Sistema di Presentazione XML

La UI si definisce in XML, renderizzato in HTML/Tailwind dall'adapter di presentazione. Per l'elenco completo di tag e attributi, fai sempre riferimento a `src/application/view.md`.

**Escaping obbligatorio:** `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`.

**Tag principali:** `<Window>`, `<Navigation>`, `<Row>`/`<Column>`, `<Text>` (tipo H1-H6/p/span via attributo `type`), `<Action>`, `<Container>`, `<Divider>`, `<Icon>`, `<SVG>`. Ogni file XML in `view/component/` diventa un tag custom usabile altrove (es. `<MyCard />`), con `{{ inner | safe }}` per iniettare i children.

**Attributi comuni (mappati su Tailwind):** `width`/`height`, `padding`/`margin` (valori separati da virgola), `justify`/`align`, `background` (hex o gradiente), `matter` (`glass`, `glass-max`), `font` (`bold`, `mono`, `black`, `extrabold`).

### ⚡ Reattività Server-Driven (WebSocket)
Qualunque elemento XML può reagire a cambi di stato del DSL senza JavaScript tramite l'attributo `bind="dsl_alias:node_path"` (es. `bind="counter:counter_logic.count"`).

**Regola obbligatoria:** ogni elemento con `bind=` deve avere un `id="..."` esplicito, altrimenti il framework va in crash intenzionalmente per prevenire memory leak nel DAG.

---

## ⚙️ Configurazione `pyproject.toml`

```toml
[project]
name = "my_app"
key = "SECRET_KEY"

[project.policy]
presentation = "web.toml"  # → src/application/policy/presentation/web.toml

[presentation.backend]
adapter = "starlette"
port = "5000"
```

Ogni blocco (`persistence`, `presentation`, `message`, `manager`, ...) attiva un adapter corrispondente in `src/infrastructure/`. Il `Loader` fa discovery solo degli adapter effettivamente presenti nel file — installa via `--install`/`--setup` solo le dipendenze dichiarate nei loro contract, non un requirements.txt monolitico.

---

## 🌐 Routing e Policy

Route e regole di accesso vivono in `src/application/policy/presentation/web.toml`.

1. **Aggiungere una rotta:** entry `[[store.data.routes]]`. Il path `view` è relativo a `src/application/view/page/` — non includere il prefisso `page/` (usa `view = "portfolio.xml"`, non `view = "page/portfolio.xml"`).
2. **Definire una policy:** entry `[[policies]]`, con condizioni valutate su `input.path` / `input.principal`.

---

## 🛠️ Comandi Utili

Assicurati sempre che il virtual environment sia attivo prima di eseguire comandi.

| Comando | Effetto |
|---|---|
| `source venv/bin/activate` | Attiva il virtual environment |
| `python3 public/main.py` | Avvia il server |
| `python3 public/main.py --setup` | `pip install -e .` + installazione dipendenze degli adapter attivi — al primo avvio |
| `python3 public/main.py --install` | Installa solo le dipendenze degli adapter attivi (senza editable install) |
| `python3 public/main.py --test [FILTRO]` | Esegue i test, opzionalmente filtrati (`managers`, `ports`, `services`, `infrastructure/message`, ecc.) |
| `python3 public/main.py --dev` | Modalità dev: disattiva il controllo strict dei contract |
| `python3 public/main.py --skip-verify` | Bypassa il controllo "codice testato" — solo per emergenze umane, mai come default in un workflow LLM |

---

## 🚀 Workflow per Agenti — riepilogo end-to-end

1. **Stabilisci la modalità** (App Builder o Framework Maintenance) e rispetta il relativo scope.
2. **Se serve nuova logica di dominio:** definisci il modello in `src/application/model/`, scrivi l'azione in `.dsl` (consultando `dsl.md`), costruisci la vista in `.xml` (consultando `view.md`).
3. **Se stai modificando un manager esistente (Framework Maintenance Mode):** scrivi/aggiorna il `*.test.dsl` per primo, poi implementa, poi verifica con `--test <filtro>` — mai saltare questo passaggio.
4. **Controlla contro la lista degli anti-pattern** prima di considerare il lavoro finito: nessun metodo `_2`, nessun init fantasma, nessun identificatore in italiano, naming CRUD coerente, nessun debug residuo.
5. **Collega tutto in `pyproject.toml`** se hai aggiunto un nuovo adapter o modificato la configurazione.
6. **Un commit per componente**, con il contract aggiornato incluso nel commit.
