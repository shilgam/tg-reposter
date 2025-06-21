## Structured Description of CLI Script Logic

> **Purpose:** Automate copying—and, when necessary, deleting—messages between Telegram channels using Python + Telethon.

### 1. Base Directories

* **Input files:** `./temp/input/`
* **Output files:** `./temp/output/`

### 2. Usage Scenarios

1. **Human-in-the-loop**

   1. Run `make repost` — the operator verifies the publication.
   2. Run `make delete` — the operator verifies the deletion.
2. **Fully automatic mode**

   * A single run of `make sync`, which executes both steps sequentially without human intervention.

> *Assumption:* the contents of `source_urls.txt` remain unchanged between runs.

### 3. The `make repost` Command

#### 3.1. File Preparation

* If `new_dest_urls.txt` is missing, create an empty file.
* If the file exists and is not empty:

  * Create a copy named `{TIMESTAMP}-old_dest_urls.txt` (e.g., `20250622_001530_old_dest_urls.txt`).
  * Clear the original `new_dest_urls.txt`.

#### 3.2. Main Algorithm

1. Read all links from `source_urls.txt`.
2. For each link:

   * Post a new message to the public channel.
   * Immediately append the URL of the new message to `new_dest_urls.txt`.
3. If any error or exception occurs, stop execution immediately and do **not** proceed to subsequent links.

### 4. The `make delete` Command

#### 4.1. Selecting the List File

* **Without an argument** — in `./temp/output/`, find the most recent file whose name contains `old_dest_urls`.
* **With the `LIST=<path/name>` argument** — use the explicitly provided file.

#### 4.2. Deletion Algorithm

1. Read all URLs from the chosen file.
2. Delete each message in the public channel.
3. After successfully deleting all messages, rename the file by replacing the `_dest_urls` suffix with `deleted`
   (e.g., `20250621_142359_123_deleted.txt`).

### 5. The `make sync` Command

1. Executes the entire `make repost` logic.
2. Upon success, automatically runs `make delete`, using the generated `*-old_dest_urls.txt` file.

### 6. Error Handling

* Any unhandled error aborts the current command.
* Logs and stack traces are printed to the console; the exit code reflects the status for automation (`make sync`).

### 7. Resulting Artifacts

* **`make repost`**

  * Updated `new_dest_urls.txt` containing links to new posts.
  * (Optionally) an archived `{TIMESTAMP}-old_dest_urls.txt`, if one was created.
* **`make delete`**

  * Renamed file `{TIMESTAMP}_deleted.txt`, confirming deletion.
* **`make sync`**

  * A combination of all artifacts above; the history of deleted messages is fully cleared.

### 8. Quick Developer Checklist

* Create and rename files atomically to prevent data loss.
* Abort execution on any error; do not continue the loop.
* Produce informative logs at every step.
* Accept `SRC=` and `LIST=` parameters from environment variables or CLI flags.
* Cover with tests: empty files, partial failures, invalid paths.
