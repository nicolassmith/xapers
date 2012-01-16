; xapers.el --- run xapers within emacs
;
; Copyright © Carl Worth
;
; This file is part of Xapers.
;
; Xapers is free software: you can redistribute it and/or modify it
; under the terms of the GNU General Public License as published by
; the Free Software Foundation, either version 3 of the License, or
; (at your option) any later version.
;
; Xapers is distributed in the hope that it will be useful, but
; WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
; General Public License for more details.
;
; You should have received a copy of the GNU General Public License
; along with Xapers.  If not, see <http://www.gnu.org/licenses/>.
;
; Authors: Carl Worth <cworth@cworth.org>

; This is an emacs-based interface to the xapers mail system.
;
; You will first need to have the xapers program installed and have a
; xapers database built in order to use this. See
; http://xapersmail.org for details.
;
; To install this software, copy it to a directory that is on the
; `load-path' variable within emacs (a good candidate is
; /usr/local/share/emacs/site-lisp). If you are viewing this from the
; xapers source distribution then you can simply run:
;
;	sudo make install-emacs
;
; to install it.
;
; Then, to actually run it, add:
;
;	(require 'xapers)
;
; to your ~/.emacs file, and then run "M-x xapers" from within emacs,
; or run:
;
;	emacs -f xapers
;
; Have fun, and let us know if you have any comment, questions, or
; kudos: Xapers list <xapers@xapersmail.org> (subscription is not
; required, but is available from http://xapersmail.org).

(eval-when-compile (require 'cl))

(require 'xapers-lib)

(defcustom xapers-search-result-format
  `(("percent" . "%3s ")
    ("file" . "%s ")
    ("tags" . "(%s)")
    ("summary" . "%s")
    )
  "Search result formatting. Supported fields are:
	date, count, authors, subject, tags
For example:
	(setq xapers-search-result-format \(\(\"authors\" . \"%-40s\"\)
					     \(\"subject\" . \"%s\"\)\)\)"
  :type '(alist :key-type (string) :value-type (string))
  :group 'xapers)

(defvar xapers-query-history nil
  "Variable to store minibuffer history for xapers queries")

(defun xapers-select-tag-with-completion (prompt &rest search-terms)
  (let ((tag-list
	 (with-output-to-string
	   (with-current-buffer standard-output
	     (apply 'call-process xapers-command nil t nil "search-tags" search-terms)))))
    (completing-read prompt (split-string tag-list "\n+" t) nil nil nil)))

(defun xapers-documentation-first-line (symbol)
  "Return the first line of the documentation string for SYMBOL."
  (let ((doc (documentation symbol)))
    (if doc
	(with-temp-buffer
	  (insert (documentation symbol t))
	  (goto-char (point-min))
	  (let ((beg (point)))
	    (end-of-line)
	    (buffer-substring beg (point))))
      "")))

(defun xapers-prefix-key-description (key)
  "Given a prefix key code, return a human-readable string representation.

This is basically just `format-kbd-macro' but we also convert ESC to M-."
  (let ((desc (format-kbd-macro (vector key))))
    (if (string= desc "ESC")
	"M-"
      (concat desc " "))))

; I would think that emacs would have code handy for walking a keymap
; and generating strings for each key, and I would prefer to just call
; that. But I couldn't find any (could be all implemented in C I
; suppose), so I wrote my own here.
(defun xapers-substitute-one-command-key-with-prefix (prefix binding)
  "For a key binding, return a string showing a human-readable
representation of the prefixed key as well as the first line of
documentation from the bound function.

For a mouse binding, return nil."
  (let ((key (car binding))
	(action (cdr binding)))
    (if (mouse-event-p key)
	nil
      (if (keymapp action)
	  (let ((substitute (apply-partially 'xapers-substitute-one-command-key-with-prefix (xapers-prefix-key-description key)))
		(as-list))
	    (map-keymap (lambda (a b)
			  (push (cons a b) as-list))
			action)
	    (mapconcat substitute as-list "\n"))
	(concat prefix (format-kbd-macro (vector key))
		"\t"
		(xapers-documentation-first-line action))))))

(defalias 'xapers-substitute-one-command-key
  (apply-partially 'xapers-substitute-one-command-key-with-prefix nil))

(defun xapers-substitute-command-keys (doc)
  "Like `substitute-command-keys' but with documentation, not function names."
  (let ((beg 0))
    (while (string-match "\\\\{\\([^}[:space:]]*\\)}" doc beg)
      (let ((map (substring doc (match-beginning 1) (match-end 1))))
	(setq doc (replace-match (mapconcat 'xapers-substitute-one-command-key
					    (cdr (symbol-value (intern map))) "\n") 1 1 doc)))
      (setq beg (match-end 0)))
    doc))

(defun xapers-help ()
  "Display help for the current xapers mode."
  (interactive)
  (let* ((mode major-mode)
	 (doc (substitute-command-keys (xapers-substitute-command-keys (documentation mode t)))))
    (with-current-buffer (generate-new-buffer "*xapers-help*")
      (insert doc)
      (goto-char (point-min))
      (set-buffer-modified-p nil)
      (view-buffer (current-buffer) 'kill-buffer-if-not-modified))))

(defcustom xapers-search-hook '(hl-line-mode)
  "List of functions to call when xapers displays the search results."
  :type 'hook
  :options '(hl-line-mode)
  :group 'xapers)

(defvar xapers-search-mode-map
  (let ((map (make-sparse-keymap)))
    (define-key map [mouse-1] 'xapers-search-show-entry)
    (define-key map "?" 'xapers-help)
    (define-key map "q" 'xapers-search-quit)
    (define-key map "s" 'xapers-search)
    (define-key map (kbd "<DEL>") 'xapers-search-scroll-down)
    (define-key map " " 'xapers-search-scroll-up)
    (define-key map "<" 'xapers-search-first-entry)
    (define-key map ">" 'xapers-search-last-entry)
    (define-key map "p" 'xapers-search-previous-entry)
    (define-key map "n" 'xapers-search-next-entry)
    (define-key map "o" 'xapers-search-toggle-order)
    (define-key map "c" 'xapers-search-stash-map)
    (define-key map "=" 'xapers-search-refresh-view)
    (define-key map "G" 'xapers-search-poll-and-refresh-view)
    (define-key map "t" 'xapers-search-filter-by-tag)
    (define-key map "f" 'xapers-search-filter)
    (define-key map "*" 'xapers-search-operate-all)
    (define-key map "-" 'xapers-search-remove-tag)
    (define-key map "+" 'xapers-search-add-tag)
    (define-key map "a" 'xapers-search-archive)
    (define-key map (kbd "RET") 'xapers-search-open)
    map)
  "Keymap for \"xapers search\" buffers.")
(fset 'xapers-search-mode-map xapers-search-mode-map)

(defvar xapers-search-stash-map
  (let ((map (make-sparse-keymap)))
    (define-key map "i" 'xapers-search-stash-docid)
    (define-key map "f" 'xapers-search-stash-file)
    map)
  "Submap for stash commands")
(fset 'xapers-search-stash-map xapers-search-stash-map)

(defun xapers-search-stash-docid ()
  "Copy file docid to kill-ring."
  (interactive)
  (xapers-common-do-stash (xapers-search-find-docid)))

(defun xapers-search-stash-file ()
  "Copy file path to kill-ring."
  (interactive)
  (xapers-common-do-stash (xapers-search-find-file)))

(defvar xapers-search-query-string)
(defvar xapers-search-target-entry)
(defvar xapers-search-target-line)
(defvar xapers-search-continuation)

(defvar xapers-search-disjunctive-regexp      "\\<[oO][rR]\\>")

(defun xapers-search-quit ()
  "Exit the search buffer, calling any defined continuation function."
  (interactive)
  (let ((continuation xapers-search-continuation))
    (when (not (string= "*xapers-search-tag:inbox*" (buffer-name)))
      (xapers-kill-this-buffer)
      (when continuation
	  (funcall continuation)))))
;      (kill-emacs))))

(defun xapers-search-scroll-up ()
  "Move forward through search results by one window's worth."
  (interactive)
  (condition-case nil
      (scroll-up nil)
    ((end-of-buffer) (xapers-search-last-entry))))

(defun xapers-search-scroll-down ()
  "Move backward through the search results by one window's worth."
  (interactive)
  ; I don't know why scroll-down doesn't signal beginning-of-buffer
  ; the way that scroll-up signals end-of-buffer, but c'est la vie.
  ;
  ; So instead of trapping a signal we instead check whether the
  ; window begins on the first line of the buffer and if so, move
  ; directly to that position. (We have to count lines since the
  ; window-start position is not the same as point-min due to the
  ; invisible entry-ID characters on the first line.
  (if (equal (count-lines (point-min) (window-start)) 0)
      (goto-char (point-min))
    (scroll-down nil)))

(defun xapers-search-next-entry ()
  "Select the next entry in the search results."
  (interactive)
  (forward-line 7))

(defun xapers-search-previous-entry ()
  "Select the previous entry in the search results."
  (interactive)
  (forward-line -7))

(defun xapers-search-last-entry ()
  "Select the last entry in the search results."
  (interactive)
  (goto-char (point-max))
  (forward-line -1)
  (xapers-search-previous-entry))

(defun xapers-search-first-entry ()
  "Select the first entry in the search results."
  (interactive)
  (goto-char (point-min)))

(defface xapers-search-percent
  '((t :inherit default :foreground "yellow"))
  "Face used in search mode for match percent."
  :group 'xapers)

(defface xapers-search-file
  '((t :inherit default :foreground "blue"))
  "Face used in search mode for file."
  :group 'xapers)

(defface xapers-search-summary
  '((t :inherit default :foreground "green"))
  "Face used in search mode for file."
  :group 'xapers)

(defface xapers-search-date
  '((t :inherit default))
  "Face used in search mode for dates."
  :group 'xapers)

(defface xapers-search-subject
  '((t :inherit default))
  "Face used in search mode for subjects."
  :group 'xapers)

(defface xapers-search-matching-authors
  '((t :inherit default))
  "Face used in search mode for authors matching the query."
  :group 'xapers)

(defface xapers-search-non-matching-authors
  '((((class color)
      (background dark))
     (:foreground "grey30"))
    (((class color)
      (background light))
     (:foreground "grey60"))
    (t
     (:italic t)))
  "Face used in search mode for authors not matching the query."
  :group 'xapers)

(defface xapers-tag-face
  '((((class color)
      (background dark))
     (:foreground "OliveDrab1"))
    (((class color)
      (background light))
     (:foreground "navy blue" :bold t))
    (t
     (:bold t)))
  "Face used in search mode face for tags."
  :group 'xapers)

(defun xapers-search-mode ()
  "Major mode displaying results of a xapers search.

This buffer contains the results of a \"xapers search\" of your
email archives. Each line in the buffer represents a single
entry giving a summary of the entry (a relative date, the
number of matched messages and total messages in the entry,
participants in the entry, a representative subject line, and
any tags).

Pressing \\[xapers-search-show-entry] on any line displays that entry. The '\\[xapers-search-add-tag]' and '\\[xapers-search-remove-tag]'
keys can be used to add or remove tags from a entry. The '\\[xapers-search-archive-entry]' key
is a convenience for archiving a entry (removing the \"inbox\"
tag). The '\\[xapers-search-operate-all]' key can be used to add or remove a tag from all
entrys in the current buffer.

Other useful commands are '\\[xapers-search-filter]' for filtering the current search
based on an additional query string, '\\[xapers-search-filter-by-tag]' for filtering to include
only messages with a given tag, and '\\[xapers-search]' to execute a new, global
search.

Complete list of currently available key bindings:

\\{xapers-search-mode-map}"
  (interactive)
  (kill-all-local-variables)
  (make-local-variable 'xapers-search-query-string)
  (make-local-variable 'xapers-search-target-entry)
  (make-local-variable 'xapers-search-target-line)
  (set (make-local-variable 'xapers-search-continuation) nil)
  (set (make-local-variable 'scroll-preserve-screen-position) t)
  (add-to-invisibility-spec (cons 'ellipsis t))
  (use-local-map xapers-search-mode-map)
  (setq truncate-lines t)
  (setq major-mode 'xapers-search-mode
	mode-name "xapers-search")
  (setq buffer-read-only t))

(defun xapers-search-properties-in-region (property beg end)
  (save-excursion
    (let ((output nil)
	  (last-line (line-number-at-pos end))
	  (max-line (- (line-number-at-pos (point-max)) 2)))
      (goto-char beg)
      (beginning-of-line)
      (while (<= (line-number-at-pos) (min last-line max-line))
	(setq output (cons (get-text-property (point) property) output))
	(forward-line 1))
      output)))

(defun xapers-search-find-docid ()
  "Return the docid for the current entry"
  (get-text-property (point) 'xapers-search-docid))

(defun xapers-search-find-docid-region (beg end)
  "Return a list of docid for the current region"
  (xapers-search-properties-in-region 'xapers-search-docid beg end))

(defun xapers-search-find-file ()
  "Return the entry for the current entry"
  (get-text-property (point) 'xapers-search-file))

(defun xapers-search-find-authors ()
  "Return the authors for the current entry"
  (get-text-property (point) 'xapers-search-authors))

(defun xapers-search-find-authors-region (beg end)
  "Return a list of authors for the current region"
  (xapers-search-properties-in-region 'xapers-search-authors beg end))

(defun xapers-search-find-subject ()
  "Return the subject for the current entry"
  (get-text-property (point) 'xapers-search-subject))

(defun xapers-search-find-subject-region (beg end)
  "Return a list of authors for the current region"
  (xapers-search-properties-in-region 'xapers-search-subject beg end))

(defun xapers-search-open ()
  "View/see file."
  (interactive)
  (let ((file (xapers-search-find-file)))
    (start-process file nil "see" file)))

(defun xapers-call-xapers-process (&rest args)
  "Synchronously invoke \"xapers\" with the given list of arguments.

Output from the process will be presented to the user as an error
and will also appear in a buffer named \"*xapers errors*\"."
  (let ((error-buffer (get-buffer-create "*xapers errors*")))
    (with-current-buffer error-buffer
	(erase-buffer))
    (if (eq (apply 'call-process xapers-command nil error-buffer nil args) 0)
	(point)
      (progn
	(with-current-buffer error-buffer
	  (let ((beg (point-min))
		(end (- (point-max) 1)))
	    (error (buffer-substring beg end))
	    ))))))

(defun xapers-tag (query &rest tags)
  "Add/remove tags in TAGS to messages matching QUERY.

TAGS should be a list of strings of the form \"+TAG\" or \"-TAG\" and
QUERY should be a string containing the search-query.

Note: Other code should always use this function alter tags of
messages instead of running (xapers-call-xapers-process \"tag\" ..)
directly, so that hooks specified in xapers-before-tag-hook and
xapers-after-tag-hook will be run."
  (run-hooks 'xapers-before-tag-hook)
  (apply 'xapers-call-xapers-process
	 (append (list "tag") tags (list "--" query)))
  (run-hooks 'xapers-after-tag-hook))

(defcustom xapers-before-tag-hook nil
  "Hooks that are run before tags of a message are modified.

'tags' will contain the tags that are about to be added or removed as
a list of strings of the form \"+TAG\" or \"-TAG\".
'query' will be a string containing the search query that determines
the messages that are about to be tagged"

  :type 'hook
  :options '(hl-line-mode)
  :group 'xapers)

(defcustom xapers-after-tag-hook nil
  "Hooks that are run after tags of a message are modified.

'tags' will contain the tags that were added or removed as
a list of strings of the form \"+TAG\" or \"-TAG\".
'query' will be a string containing the search query that determines
the messages that were tagged"
  :type 'hook
  :options '(hl-line-mode)
  :group 'xapers)

(defun xapers-search-set-tags (tags)
  (save-excursion
    (end-of-line)
    (re-search-backward "(")
    (forward-char)
    (let ((beg (point))
	  (inhibit-read-only t))
      (re-search-forward ")")
      (backward-char)
      (let ((end (point)))
	(delete-region beg end)
	(insert (propertize (mapconcat  'identity tags " ")
			    'face 'xapers-tag-face))))))

(defun xapers-search-get-tags ()
  (save-excursion
    (end-of-line)
    (re-search-backward "(")
    (let ((beg (+ (point) 1)))
      (re-search-forward ")")
      (let ((end (- (point) 1)))
	(split-string (buffer-substring beg end))))))

(defun xapers-search-get-tags-region (beg end)
  (save-excursion
    (let ((output nil)
	  (last-line (line-number-at-pos end))
	  (max-line (- (line-number-at-pos (point-max)) 2)))
      (goto-char beg)
      (while (<= (line-number-at-pos) (min last-line max-line))
	(setq output (append output (xapers-search-get-tags)))
	(forward-line 1))
      output)))

(defun xapers-search-add-tag-region (tag beg end)
  (let ((search-id-string (mapconcat 'identity (xapers-search-find-docid-region beg end) " or ")))
    (xapers-tag search-id-string (concat "+" tag))
    (save-excursion
      (let ((last-line (line-number-at-pos end))
	    (max-line (- (line-number-at-pos (point-max)) 2)))
	(goto-char beg)
	(while (<= (line-number-at-pos) (min last-line max-line))
	  (xapers-search-set-tags (delete-dups (sort (cons tag (xapers-search-get-tags)) 'string<)))
	  (forward-line))))))

(defun xapers-search-remove-tag-region (tag beg end)
  (let ((search-id-string (mapconcat 'identity (xapers-search-find-docid-region beg end) " or ")))
    (xapers-tag search-id-string (concat "-" tag))
    (save-excursion
      (let ((last-line (line-number-at-pos end))
	    (max-line (- (line-number-at-pos (point-max)) 2)))
	(goto-char beg)
	(while (<= (line-number-at-pos) (min last-line max-line))
	  (xapers-search-set-tags (delete tag (xapers-search-get-tags)))
	  (forward-line))))))

(defun xapers-search-add-tag (tag)
  "Add a tag to the currently selected entry or region.

The tag is added to all messages in the currently selected entry
or entrys in the current region."
  (interactive
   (list (xapers-select-tag-with-completion "Tag to add: ")))
  (save-excursion
    (if (region-active-p)
	(let* ((beg (region-beginning))
	       (end (region-end)))
	  (xapers-search-add-tag-region tag beg end))
      (xapers-search-add-tag-region tag (point) (point)))))

(defun xapers-search-remove-tag (tag)
  "Remove a tag from the currently selected entry or region.

The tag is removed from all messages in the currently selected
entry or entrys in the current region."
  (interactive
   (list (xapers-select-tag-with-completion
	  "Tag to remove: "
	  (if (region-active-p)
	      (mapconcat 'identity
			 (xapers-search-find-docid-region (region-beginning) (region-end))
			 " ")
	    (xapers-search-find-docid)))))
  (save-excursion
    (if (region-active-p)
	(let* ((beg (region-beginning))
	       (end (region-end)))
	  (xapers-search-remove-tag-region tag beg end))
      (xapers-search-remove-tag-region tag (point) (point)))))

(defun xapers-search-archive ()
  "Archive the currently selected entry (remove its \"inbox\" tag).

This function advances the next entry when finished."
  ;; (interactive)
  ;; (let ((file (xapers-search-find-file)))
  ;;   (start-process "xapers archive" nil "xapers" "archive" file))
  ;; (xapers-search-refresh-view))
  (interactive)
  (xapers-search-remove-tag "inbox")
  (xapers-search-next-entry))

(defvar xapers-search-process-filter-data nil
  "Data that has not yet been processed.")
(make-variable-buffer-local 'xapers-search-process-filter-data)

(defun xapers-search-process-sentinel (proc msg)
  "Add a message to let user know when \"xapers search\" exits"
  (let ((buffer (process-buffer proc))
	(status (process-status proc))
	(exit-status (process-exit-status proc))
	(never-found-target-entry nil))
    (if (memq status '(exit signal))
	(if (buffer-live-p buffer)
	    (with-current-buffer buffer
	      (save-excursion
		(let ((inhibit-read-only t)
		      (atbob (bobp)))
		  (goto-char (point-max))
		  (if (eq status 'signal)
		      (insert "Incomplete search results (search process was killed).\n"))
		  (if (eq status 'exit)
		      (progn
			(if xapers-search-process-filter-data
			    (insert (concat "Error: Unexpected output from xapers search:\n" xapers-search-process-filter-data)))
			(insert "End of search results.")
			(if (not (= exit-status 0))
			    (insert (format " (process returned %d)" exit-status)))
			(insert "\n")
			(if (and atbob
				 (not (string= xapers-search-target-entry "found")))
			    (set 'never-found-target-entry t))))))
	      (when (and never-found-target-entry
		       xapers-search-target-line)
		  (goto-char (point-min))
		  (forward-line (1- xapers-search-target-line))))))))

(defcustom xapers-search-line-faces nil
  "Tag/face mapping for line highlighting in xapers-search.

Here is an example of how to color search results based on tags.
 (the following text would be placed in your ~/.emacs file):

 (setq xapers-search-line-faces '((\"deleted\" . (:foreground \"red\"
						  :background \"blue\"))
                                   (\"unread\" . (:foreground \"green\"))))

The attributes defined for matching tags are merged, with later
attributes overriding earlier. A message having both \"deleted\"
and \"unread\" tags with the above settings would have a green
foreground and blue background."
  :type '(alist :key-type (string) :value-type (custom-face-edit))
  :group 'xapers)

(defun xapers-search-color-line (start end line-tag-list)
  "Colorize lines in `xapers-show' based on tags."
  ;; Create the overlay only if the message has tags which match one
  ;; of those specified in `xapers-search-line-faces'.
  (let (overlay)
    (mapc (lambda (elem)
	    (let ((tag (car elem))
		  (attributes (cdr elem)))
	      (when (member tag line-tag-list)
		(when (not overlay)
		  (setq overlay (make-overlay start end)))
		;; Merge the specified properties with any already
		;; applied from an earlier match.
		(overlay-put overlay 'face
			     (append (overlay-get overlay 'face) attributes)))))
	  xapers-search-line-faces)))

(defun xapers-search-author-propertize (authors)
  "Split `authors' into matching and non-matching authors and
propertize appropriately. If no boundary between authors and
non-authors is found, assume that all of the authors match."
  (if (string-match "\\(.*\\)|\\(.*\\)" authors)
      (concat (propertize (concat (match-string 1 authors) ",")
			  'face 'xapers-search-matching-authors)
	      (propertize (match-string 2 authors)
			  'face 'xapers-search-non-matching-authors))
    (propertize authors 'face 'xapers-search-matching-authors)))

(defun xapers-search-insert-authors (format-string authors)
  ;; Save the match data to avoid interfering with
  ;; `xapers-search-process-filter'.
  (save-match-data
    (let* ((formatted-authors (format format-string authors))
	   (formatted-sample (format format-string ""))
	   (visible-string formatted-authors)
	   (invisible-string "")
	   (padding ""))

      ;; Truncate the author string to fit the specification.
      (if (> (length formatted-authors)
	     (length formatted-sample))
	  (let ((visible-length (- (length formatted-sample)
				   (length "... "))))
	    ;; Truncate the visible string according to the width of
	    ;; the display string.
	    (setq visible-string (substring formatted-authors 0 visible-length)
		  invisible-string (substring formatted-authors visible-length))
	    ;; If possible, truncate the visible string at a natural
	    ;; break (comma or pipe), as incremental search doesn't
	    ;; match across the visible/invisible border.
	    (when (string-match "\\(.*\\)\\([,|] \\)\\([^,|]*\\)" visible-string)
	      ;; Second clause is destructive on `visible-string', so
	      ;; order is important.
	      (setq invisible-string (concat (match-string 3 visible-string)
					     invisible-string)
		    visible-string (concat (match-string 1 visible-string)
					   (match-string 2 visible-string))))
	    ;; `visible-string' may be shorter than the space allowed
	    ;; by `format-string'. If so we must insert some padding
	    ;; after `invisible-string'.
	    (setq padding (make-string (- (length formatted-sample)
					  (length visible-string)
					  (length "..."))
				       ? ))))

      ;; Use different faces to show matching and non-matching authors.
      (if (string-match "\\(.*\\)|\\(.*\\)" visible-string)
	  ;; The visible string contains both matching and
	  ;; non-matching authors.
	  (setq visible-string (xapers-search-author-propertize visible-string)
		;; The invisible string must contain only non-matching
		;; authors, as the visible-string contains both.
		invisible-string (propertize invisible-string
					     'face 'xapers-search-non-matching-authors))
	;; The visible string contains only matching authors.
	(setq visible-string (propertize visible-string
					 'face 'xapers-search-matching-authors)
	      ;; The invisible string may contain both matching and
	      ;; non-matching authors.
	      invisible-string (xapers-search-author-propertize invisible-string)))

      ;; If there is any invisible text, add it as a tooltip to the
      ;; visible text.
      (when (not (string= invisible-string ""))
	(setq visible-string (propertize visible-string 'help-echo (concat "..." invisible-string))))

      ;; Insert the visible and, if present, invisible author strings.
      (insert visible-string)
      (when (not (string= invisible-string ""))
	(let ((start (point))
	      overlay)
	  (insert invisible-string)
	  (setq overlay (make-overlay start (point)))
	  (overlay-put overlay 'invisible 'ellipsis)
	  (overlay-put overlay 'isearch-open-invisible #'delete-overlay)))
      (insert padding))))

(defun xapers-search-insert-summary (format-string summary)
  ;; Save the match data to avoid interfering with
  ;; `xapers-search-process-filter'.
  (save-match-data
    (insert "\n")
    (insert (propertize (format format-string summary)
			'face 'xapers-search-summary
			'line-prefix " "
			'wrap-prefix " "))
    (setq fill-column 100)
    (fill-region (line-beginning-position) (point))))

(defun xapers-search-insert-field (field percent file tags summary)
  (cond
   ((string-equal field "percent")
    (insert (propertize (format (cdr (assoc field xapers-search-result-format)) percent)
			'face 'xapers-search-percent)))
   ((string-equal field "file")
    (insert (propertize (format (cdr (assoc field xapers-search-result-format)) file)
			'face 'xapers-search-file)))
   ((string-equal field "tags")
    (insert (concat "(" (propertize tags 'font-lock-face 'xapers-tag-face) ")")))

   ((string-equal field "summary")
    (xapers-search-insert-summary (cdr (assoc field xapers-search-result-format)) summary))
   ))

(defun xapers-search-show-result (percent file tags summary)
  (let ((fields) (field))
    (setq fields (mapcar 'car xapers-search-result-format))
    (loop for field in fields
	  do (xapers-search-insert-field field percent file tags summary)))
  (insert "\n"))

;; (defun xapers-search-process-filter (proc string)
;;   "Process and filter the output of \"xapers search\""
;;   (let ((buffer (process-buffer proc))
;; 	(found-target nil))
;;     (if (buffer-live-p buffer)
;; 	(with-current-buffer buffer
;; 	  (save-excursion
;; 	    (let ((line 0)
;; 		  (more t)
;; 		  (inhibit-read-only t)
;; 		  (string (concat xapers-search-process-filter-data string)))
;; 	      (setq xapers-search-process-filter-data nil)
;; 	      (while more
;; 		(while (and (< line (length string)) (= (elt string line) ?\n))
;; 		  (setq line (1+ line)))
;; 		(if (string-match "^\\(entry:[0-9A-Fa-f]*\\) \\([^][]*\\) \\(\\[[0-9/]*\\]\\) \\([^;]*\\); \\(.*\\) (\\([^()]*\\))$" string line)
;; 		    (let* ((docid (match-string 1 string))
;; 			   (date (match-string 2 string))
;; 			   (count (match-string 3 string))
;; 			   (authors (match-string 4 string))
;; 			   (subject (match-string 5 string))
;; 			   (tags (match-string 6 string))
;; 			   (tag-list (if tags (save-match-data (split-string tags)))))
;; 		      (goto-char (point-max))
;; 		      (if (/= (match-beginning 1) line)
;; 			  (insert (concat "Error: Unexpected output from xapers search:\n" (substring string line (match-beginning 1)) "\n")))
;; 		      (let ((beg (point)))
;; 			(xapers-search-show-result date count authors subject tags)
;; 			(xapers-search-color-line beg (point) tag-list)
;; 			(put-text-property beg (point) 'xapers-search-docid docid)
;; 			(put-text-property beg (point) 'xapers-search-authors authors)
;; 			(put-text-property beg (point) 'xapers-search-subject subject)
;; 			(if (string= docid xapers-search-target-entry)
;; 			    (progn
;; 			      (set 'found-target beg)
;; 			      (set 'xapers-search-target-entry "found"))))
;; 		      (set 'line (match-end 0)))
;; 		  (set 'more nil)
;; 		  (while (and (< line (length string)) (= (elt string line) ?\n))
;; 		    (setq line (1+ line)))
;; 		  (if (< line (length string))
;; 		      (setq xapers-search-process-filter-data (substring string line)))
;; 		  ))))
;; 	  (if found-target
;; 	      (goto-char found-target)))
;;       (delete-process proc))))

(defun xapers-search-process-filter (proc string)
  "Process and filter the output of \"xapers search\""
  (let ((buffer (process-buffer proc))
	(found-target nil))
    (if (buffer-live-p buffer)
	(with-current-buffer buffer
	  (save-excursion
	    (let ((line 0)
		  (more t)
		  (inhibit-read-only t)
		  (string (concat xapers-search-process-filter-data string)))
	      (setq xapers-search-process-filter-data nil)
	      (while more
		(while (and (< line (length string)) (= (elt string line) ?\n))
		  (setq line (1+ line)))
		(if (string-match "^\\(.*\\) \\(.*\\) \\(.*\\) (\\([^()]*\\)) \"\\(.*\\)\"$" string line)
		    (let* ((docid (match-string 1 string))
			   (percent (match-string 2 string))
			   (file (match-string 3 string))
			   (tags (match-string 4 string))
			   (summary (match-string 5 string))
			   (tag-list (if tags (save-match-data (split-string tags))))
			   )
		      (goto-char (point-max))
		      (if (/= (match-beginning 1) line)
			  (insert (concat "Error: Unexpected output from xapers search:\n" (substring string line (match-beginning 1)) "\n")))
		      (let ((beg (point)))
			(xapers-search-show-result percent docid tags summary)
			;(xapers-search-color-line beg (point) tag-list)
 			(put-text-property beg (point) 'xapers-search-docid docid)
 			(put-text-property beg (point) 'xapers-search-file file)
			)
		      (set 'line (match-end 0)))
		  (set 'more nil)
		  (while (and (< line (length string)) (= (elt string line) ?\n))
		    (setq line (1+ line)))
		  (if (< line (length string))
		      (setq xapers-search-process-filter-data (substring string line)))
		  ))))
	  (if found-target
	      (goto-char found-target)))
      (delete-process proc))))

(defun xapers-search-operate-all (action)
  "Add/remove tags from all matching messages.

This command adds or removes tags from all messages matching the
current search terms. When called interactively, this command
will prompt for tags to be added or removed. Tags prefixed with
'+' will be added and tags prefixed with '-' will be removed.

Each character of the tag name may consist of alphanumeric
characters as well as `_.+-'.
"
  (interactive "sOperation (+add -drop): xapers tag ")
  (let ((action-split (split-string action " +")))
    ;; Perform some validation
    (let ((words action-split))
      (when (null words) (error "No operation given"))
      (while words
	(unless (string-match-p "^[-+][-+_.[:word:]]+$" (car words))
	  (error "Action must be of the form `+thistag -that_tag'"))
	(setq words (cdr words))))
    (apply 'xapers-tag xapers-search-query-string action-split)))

(defun xapers-search-buffer-title (query)
  "Returns the title for a buffer with xapers search results."
  (let* ((saved-search
	  (let (longest
		(longest-length 0))
	    (loop for tuple in xapers-saved-searches
		  if (let ((quoted-query (regexp-quote (cdr tuple))))
		       (and (string-match (concat "^" quoted-query) query)
			    (> (length (match-string 0 query))
			       longest-length)))
		  do (setq longest tuple))
	    longest))
	 (saved-search-name (car saved-search))
	 (saved-search-query (cdr saved-search)))
    (cond ((and saved-search (equal saved-search-query query))
	   ;; Query is the same as saved search (ignoring case)
	   (concat "*xapers-saved-search-" saved-search-name "*"))
	  (saved-search
	   (concat "*xapers-search-"
		   (replace-regexp-in-string (concat "^" (regexp-quote saved-search-query))
					     (concat "[ " saved-search-name " ]")
					     query)
		   "*"))
	  (t
	   (concat "*xapers-search-" query "*"))
	  )))

(defun xapers-read-query (prompt)
  "Read a xapers-query from the minibuffer with completion.

PROMPT is the string to prompt with."
  (lexical-let
      ((completions
	(append (list "folder:" "entry:" "id:" "date:" "from:" "to:"
		      "subject:" "attachment:")
		(mapcar (lambda (tag)
			  (concat "tag:" tag))
			(process-lines xapers-command "search" "*")))))
    (let ((keymap (copy-keymap minibuffer-local-map))
	  (minibuffer-completion-table
	   (completion-table-dynamic
	    (lambda (string)
	      ;; generate a list of possible completions for the current input
	      (cond
	       ;; this ugly regexp is used to get the last word of the input
	       ;; possibly preceded by a '('
	       ((string-match "\\(^\\|.* (?\\)\\([^ ]*\\)$" string)
		(mapcar (lambda (compl)
			  (concat (match-string-no-properties 1 string) compl))
			(all-completions (match-string-no-properties 2 string)
					 completions)))
	       (t (list string)))))))
      ;; this was simpler than convincing completing-read to accept spaces:
      (define-key keymap (kbd "<tab>") 'minibuffer-complete)
      (read-from-minibuffer prompt nil keymap nil
			    'xapers-query-history nil nil))))

;;;###autoload
(defun xapers-search (query &optional target-entry target-line continuation)
  "Run \"xapers search\" with the given query string and display results.

The optional parameters are used as follows:

  target-entry: A entry ID (with the entry: prefix) that will be made
                 current if it appears in the search results.
  target-line: The line number to move to if the target entry does not
               appear in the search results."
  ;(interactive (list (xapers-read-query "Xapers search: ")))
  (interactive "sxapers search: ")
  (let ((buffer (get-buffer-create (xapers-search-buffer-title query))))
    (switch-to-buffer buffer)
    (xapers-search-mode)
    ;; Don't track undo information for this buffer
    (set 'buffer-undo-list t)
    (set 'xapers-search-query-string query)
    (set 'xapers-search-target-entry target-entry)
    (set 'xapers-search-target-line target-line)
    (set 'xapers-search-continuation continuation)
    (let ((proc (get-buffer-process (current-buffer)))
	  (inhibit-read-only t))
      (if proc
	  (error "xapers search process already running for query `%s'" query)
	)
      (erase-buffer)
      (goto-char (point-min))
      (save-excursion
	(let ((proc (start-process
		     "xapers-search" buffer
		     xapers-command "search"
		     query)))
	  (set-process-sentinel proc 'xapers-search-process-sentinel)
	  (set-process-filter proc 'xapers-search-process-filter)
	  (set-process-query-on-exit-flag proc nil))))
    (run-hooks 'xapers-search-hook)))

(defun xapers-search-refresh-view ()
  "Refresh the current view.

Kills the current buffer and runs a new search with the same
query string as the current search. If the current entry is in
the new search results, then point will be placed on the same
entry. Otherwise, point will be moved to attempt to be in the
same relative position within the new buffer."
  (interactive)
  (let ((target-line (line-number-at-pos))
	(target-entry (xapers-search-find-docid))
	(query xapers-search-query-string)
	(continuation xapers-search-continuation))
    (xapers-kill-this-buffer)
    (xapers-search query target-entry target-line continuation)
    (goto-char (point-min))))

(defun xapers-search-filter (query)
  "Filter the current search results based on an additional query string.

Runs a new search matching only messages that match both the
current search results AND the additional query string provided."
  ;(interactive (list (xapers-read-query "Filter search: ")))
  (interactive "sfilter search: ")
  (let ((grouped-query (if (string-match-p xapers-search-disjunctive-regexp query)
			   (concat "( " query " )")
			 query)))
    (xapers-search (if (string= xapers-search-query-string "*")
			grouped-query
		      (concat xapers-search-query-string " and " grouped-query)))))

(defun xapers-search-filter-by-tag (tag)
  "Filter the current search results based on a single tag.

Runs a new search matching only messages that match both the
current search results AND that are tagged with the given tag."
  (interactive
   (list (xapers-select-tag-with-completion "Filter by tag: ")))
  (xapers-search (concat xapers-search-query-string " and tag:" tag)))

;;;###autoload
(defun xapers ()
  "Run xapers and display saved searches, known tags, etc."
  (interactive)
  (xapers-hello))

;;;###autoload
(defun xapers-jump-to-recent-buffer ()
  "Jump to the most recent xapers buffer (search, show or hello).

If no recent buffer is found, run `xapers'."
  (interactive)
  (let ((last
	 (loop for buffer in (buffer-list)
	       if (with-current-buffer buffer
		    (memq major-mode '(xapers-show-mode
				       xapers-search-mode
				       xapers-hello-mode)))
	       return buffer)))
    (if last
	(switch-to-buffer last)
      (xapers))))

(setq mail-user-agent 'xapers-user-agent)

(define-key xapers-search-mode-map "1"
  (lambda ()
    "inbox"
    (interactive)
    (xapers-search "tag:inbox" t)))

(provide 'xapers)
