# Known issues

## Bugs

- **Type radio shows a stale selection.** After **close person**, the screen can show
  **assets** selected while the tool has no type, so **save** stays disabled.
  Workaround: click **liabilities**, then **assets**. Not reproduced on demand yet.
- **Flaky browser test after a restart.**
  `test_restart_resumes_on_last_page_with_no_person` fails about 2 runs in 5: **save**
  stays disabled. Possibly the same bug as above.
- **Flaky browser test after edit.** `test_edit_replaces_block_in_place` failed once in
  CI: after **edit**, the value input stayed empty ([#11](https://github.com/nlesc-rags2riches/vox-paginae/issues/11)).

## Accepted limits of the MVP

- A closed person cannot be reopened from the screen; edit the file by hand.
- Restarting may land earlier than where you stopped, for example on a finished book
  when nothing is saved yet in the next one.
- A person named but never saved is lost on restart.
- Restarting in the middle of a deed splits it into two person files. Merge them by
  hand.
- A new person's first page is the page of their first saved block, which may be later
  than where the deed starts.
- The jump slider, thumbnail strip and folder bar are a trial and may go away.
- Not yet checked on all of Windows, macOS and Linux.
