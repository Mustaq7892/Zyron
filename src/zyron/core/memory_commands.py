class MemoryCommandHandler:
    """
    Handles explicit user-controlled permanent memory commands.

    Supported commands:

        What do you remember about me?
        What do you remember?
        Remember that ...
        Remember, that ...
        Remember, ...
        Save that ...
        Forget that ...
        Forget, that ...
        Forget, ...
        Delete that memory ...
        Forget everything you remember about me.

    The handler deliberately avoids guessing ambiguous commands.
    """

    def __init__(self, memory, user_name="User"):
        self.memory = memory
        self.user_name = user_name or "User"

    # ========================================================
    # MAIN HANDLER
    # ========================================================

    def handle(self, command):
        """
        Process a memory-related command.

        Returns:
            Response string if this is a memory command.
            None if this is not a memory command.
        """

        if command is None:
            return None

        text = str(command).strip()

        if not text:
            return None

        # ----------------------------------------------------
        # Remove repeated whitespace.
        # ----------------------------------------------------

        text = " ".join(
            text.split()
        )

        normalized = text.lower().strip()

        # ----------------------------------------------------
        # SHOW MEMORIES
        # ----------------------------------------------------

        show_commands = (
            "what do you remember about me",
            "what do you remember",
            "what memories do you have about me",
            "what memories do you have",
            "show my memories",
            "list my memories",
            "tell me what you remember about me",
        )

        if normalized in show_commands:

            return self._show_memories()

        # ----------------------------------------------------
        # FORGET EVERYTHING
        # ----------------------------------------------------

        forget_all_commands = (
            "forget everything you remember about me",
            "forget everything about me",
            "forget all my memories",
            "delete all my memories",
            "clear all my memories",
        )

        if normalized in forget_all_commands:

            return self._forget_all()

        # ----------------------------------------------------
        # REMEMBER
        # ----------------------------------------------------

        remember_prefixes = (
            "please remember that ",
            "please remember ",
            "remember that ",
            "remember, that ",
            "remember, ",
            "remember ",
            "save that ",
            "save, that ",
            "save, ",
            "save ",
        )

        for prefix in remember_prefixes:

            if normalized.startswith(prefix):

                content = text[
                    len(prefix):
                ].strip()

                return self._remember(
                    content
                )

        # ----------------------------------------------------
        # FORGET SPECIFIC MEMORY
        # ----------------------------------------------------

        forget_prefixes = (
            "please forget that ",
            "please forget ",
            "forget that ",
            "forget, that ",
            "forget, ",
            "forget ",
            "forgot that ",
            "forgot, that ",
            "forgot, ",
            "forgot ",
            "delete that memory ",
            "delete memory ",
            "delete that ",
            "delete ",
        )

        for prefix in forget_prefixes:

            if normalized.startswith(prefix):

                content = text[
                    len(prefix):
                ].strip()

                return self._forget_specific(
                    content
                )

        # ----------------------------------------------------
        # NOT A MEMORY COMMAND
        # ----------------------------------------------------

        return None

    # ========================================================
    # NORMALIZE MEMORY CONTENT
    # ========================================================

    def _normalize_memory_content(
        self,
        content,
    ):
        """
        Convert common first-person expressions into a
        permanent-memory representation.

        Examples:

            I am learning SQL Server.
                ->
            Mustaq is learning SQL Server.

            I like building Zyron.
                ->
            Mustaq likes building Zyron.

            My favorite color is blue.
                ->
            Mustaq's favorite color is blue.
        """

        content = content.strip()

        if not content:
            return ""

        # ----------------------------------------------------
        # Remove leading comma.
        #
        # Handles Whisper output such as:
        #
        #     that, I am learning SQL Server
        #
        # after the command parser has already removed
        # "remember".
        # ----------------------------------------------------

        content = content.lstrip(
            " ,"
        ).strip()

        # ----------------------------------------------------
        # Remove accidental "that" left by speech recognition.
        #
        # Examples:
        #
        #     that I am learning Python
        #     that, I am learning Python
        #
        # ----------------------------------------------------

        lower = content.lower()

        if lower.startswith(
            "that "
        ):

            content = content[5:].strip()

        elif lower.startswith(
            "that, "
        ):

            content = content[6:].strip()

        # ----------------------------------------------------
        # Remove leading punctuation.
        # ----------------------------------------------------

        content = content.lstrip(
            " ,.-"
        ).strip()

        if not content:
            return ""

        lower = content.lower()

        user_name = self.user_name.strip()

        # ----------------------------------------------------
        # First-person forms.
        # ----------------------------------------------------

        if lower.startswith(
            "i am "
        ):

            return (
                user_name
                + " is "
                + content[5:].strip()
            )

        if lower.startswith(
            "i'm "
        ):

            return (
                user_name
                + " is "
                + content[4:].strip()
            )

        if lower.startswith(
            "i have "
        ):

            return (
                user_name
                + " has "
                + content[7:].strip()
            )

        if lower.startswith(
            "i like "
        ):

            return (
                user_name
                + " likes "
                + content[7:].strip()
            )

        if lower.startswith(
            "i love "
        ):

            return (
                user_name
                + " loves "
                + content[7:].strip()
            )

        if lower.startswith(
            "i prefer "
        ):

            return (
                user_name
                + " prefers "
                + content[9:].strip()
            )

        if lower.startswith(
            "i enjoy "
        ):

            return (
                user_name
                + " enjoys "
                + content[8:].strip()
            )

        if lower.startswith(
            "my "
        ):

            return (
                user_name
                + "'s "
                + content[3:].strip()
            )

        # ----------------------------------------------------
        # Already normalized.
        # ----------------------------------------------------

        if lower.startswith(
            user_name.lower()
        ):

            return content

        # ----------------------------------------------------
        # If the user supplied another person's name or a
        # complete subject, preserve it.
        #
        # Example:
        #
        #     Hina is learning SQL Server
        #
        # stays:
        #
        #     Hina is learning SQL Server
        # ----------------------------------------------------

        if self._looks_like_named_statement(
            content
        ):

            return content

        # ----------------------------------------------------
        # Do NOT create garbage such as:
        #
        #     Mustaq: about meeting
        #
        # from incomplete commands.
        #
        # Instead, return the content unchanged here and let
        # _remember() reject it if it is incomplete.
        # ----------------------------------------------------

        return (
            user_name
            + ": "
            + content
        )

    # ========================================================
    # NAMED STATEMENT DETECTION
    # ========================================================

    def _looks_like_named_statement(
        self,
        content,
    ):
        """
        Detect simple complete statements that already have
        a subject.

        Example:

            Hina is learning SQL Server.
            John likes Python.
            Mustaq works at Infotrack.

        This is intentionally conservative.
        """

        words = content.split()

        if len(words) < 3:
            return False

        first = words[0]

        # Avoid treating pronouns as names.
        if first.lower() in {
            "i",
            "you",
            "he",
            "she",
            "they",
            "we",
            "it",
            "my",
            "that",
        }:
            return False

        second = words[1].lower()

        statement_verbs = {
            "is",
            "am",
            "are",
            "has",
            "have",
            "likes",
            "loves",
            "prefers",
            "enjoys",
            "works",
            "uses",
            "studies",
            "learns",
            "learning",
        }

        return second in statement_verbs

    # ========================================================
    # NORMALIZE QUERY
    # ========================================================

    def _normalize_query(
        self,
        content,
    ):
        """
        Normalize a user query in the same way memory content
        is normalized.

        This allows:

            Forget that I am learning SQL Server.

        to find:

            Mustaq is learning SQL Server.
        """

        if not content:
            return ""

        content = str(
            content
        ).strip()

        content = content.rstrip(
            ".,!?;:"
        ).strip()

        return self._normalize_memory_content(
            content
        ).rstrip(
            ".,!?;:"
        ).strip().lower()

    # ========================================================
    # MEMORY CONTENT NORMALIZATION FOR COMPARISON
    # ========================================================

    def _normalize_for_comparison(
        self,
        content,
    ):
        """
        Produce a normalized comparison representation.

        Differences such as:

            punctuation
            repeated spaces
            trailing periods
            capitalization

        are ignored.
        """

        if not content:
            return ""

        text = str(
            content
        ).strip().lower()

        # ----------------------------------------------------
        # Normalize whitespace.
        # ----------------------------------------------------

        text = " ".join(
            text.split()
        )

        # ----------------------------------------------------
        # Normalize punctuation.
        # ----------------------------------------------------

        text = text.rstrip(
            ".,!?;:"
        ).strip()

        # ----------------------------------------------------
        # Normalize common possessive formatting.
        # ----------------------------------------------------

        text = text.replace(
            "mustaq's ",
            "mustaq "
        )

        return text

    # ========================================================
    # SHOW MEMORIES
    # ========================================================

    def _show_memories(self):

        memories = self.memory.get_memories()

        if not memories:

            return (
                "I don't currently have any permanent "
                "memories about you."
            )

        lines = [
            "Here is what I currently remember about you:"
        ]

        for (
            memory_id,
            content,
            created_at,
        ) in memories:

            lines.append(
                f"- {content}"
            )

        return "\n".join(
            lines
        )

    # ========================================================
    # REMEMBER
    # ========================================================

    def _remember(
        self,
        content,
    ):

        content = content.strip()

        if not content:

            return (
                "What would you like me to remember?"
            )

        # ----------------------------------------------------
        # Normalize.
        # ----------------------------------------------------

        normalized_content = (
            self._normalize_memory_content(
                content
            )
        )

        if not normalized_content:

            return (
                "What would you like me to remember?"
            )

        # ----------------------------------------------------
        # Reject incomplete statements.
        #
        # Examples:
        #
        #     about meeting
        #     about work
        #     something
        #
        # These should not become permanent memories.
        # ----------------------------------------------------

        if self._is_incomplete_memory(
            normalized_content
        ):

            return (
                "What would you like me to remember?"
            )

        # ----------------------------------------------------
        # Remove trailing punctuation for consistent storage.
        # ----------------------------------------------------

        normalized_content = (
            normalized_content.rstrip(
                ".,!?;:"
            ).strip()
        )

        # ----------------------------------------------------
        # Check for duplicate.
        # ----------------------------------------------------

        existing = (
            self.memory.get_memories()
        )

        candidate = (
            self._normalize_for_comparison(
                normalized_content
            )
        )

        for (
            memory_id,
            memory_content,
            created_at,
        ) in existing:

            existing_normalized = (
                self._normalize_for_comparison(
                    memory_content
                )
            )

            if (
                existing_normalized
                == candidate
            ):

                return (
                    "I already remember that: "
                    f"{memory_content}"
                )

        # ----------------------------------------------------
        # Store.
        # ----------------------------------------------------

        self.memory.remember(
            normalized_content
        )

        return (
            "I'll remember that: "
            f"{normalized_content}"
        )

    # ========================================================
    # INCOMPLETE MEMORY DETECTION
    # ========================================================

    def _is_incomplete_memory(
        self,
        content,
    ):
        """
        Detect obviously incomplete memory requests.
        """

        text = content.strip().lower()

        if not text:
            return True

        # ----------------------------------------------------
        # Common incomplete phrases produced by Whisper.
        # ----------------------------------------------------

        incomplete_prefixes = (
            "about ",
            "something",
            "that",
            "this",
            "it",
        )

        if text in {
            "about",
            "something",
            "that",
            "this",
            "it",
        }:

            return True

        # "about meeting" is not a complete fact.
        if text.startswith(
            "about "
        ):

            return True

        # "Mustaq: about meeting"
        if (
            ": about "
            in text
        ):

            return True

        return False

    # ========================================================
    # FORGET SPECIFIC
    # ========================================================

    def _forget_specific(
        self,
        content,
    ):

        content = content.strip()

        if not content:

            return (
                "What would you like me to forget?"
            )

        # ----------------------------------------------------
        # Remove trailing punctuation.
        # ----------------------------------------------------

        content = content.rstrip(
            ".,!?;:"
        ).strip()

        if not content:

            return (
                "What would you like me to forget?"
            )

        memories = (
            self.memory.get_memories()
        )

        if not memories:

            return (
                "I don't have any permanent "
                "memories to forget."
            )

        # ----------------------------------------------------
        # Normalize the user's query.
        # ----------------------------------------------------

        normalized_query = (
            self._normalize_query(
                content
            )
        )

        if not normalized_query:

            return (
                "What would you like me to forget?"
            )

        normalized_query = (
            self._normalize_for_comparison(
                normalized_query
            )
        )

        # ----------------------------------------------------
        # Find exact normalized matches first.
        # ----------------------------------------------------

        exact_matches = []

        for (
            memory_id,
            memory_content,
            created_at,
        ) in memories:

            normalized_memory = (
                self._normalize_for_comparison(
                    memory_content
                )
            )

            if (
                normalized_memory
                == normalized_query
            ):

                exact_matches.append(
                    (
                        memory_id,
                        memory_content,
                    )
                )

        # ----------------------------------------------------
        # Exact match.
        # ----------------------------------------------------

        if exact_matches:

            deleted = 0

            for (
                memory_id,
                memory_content,
            ) in exact_matches:

                if self.memory.forget_by_id(
                    memory_id
                ):

                    deleted += 1

            if deleted == 1:

                return (
                    "I forgot the memory about "
                    f"'{content}'."
                )

            return (
                f"I forgot {deleted} memories "
                f"matching '{content}'."
            )

        # ----------------------------------------------------
        # Second pass:
        #
        # Safe substring matching.
        #
        # This handles cases such as:
        #
        #     Forget Python
        #
        # matching:
        #
        #     Mustaq is learning Python.
        #
        # But we only use this when the query has enough
        # meaningful words.
        # ----------------------------------------------------

        query_words = set(
            normalized_query.split()
        )

        if len(query_words) >= 2:

            partial_matches = []

            for (
                memory_id,
                memory_content,
                created_at,
            ) in memories:

                normalized_memory = (
                    self._normalize_for_comparison(
                        memory_content
                    )
                )

                if (
                    normalized_query
                    in normalized_memory
                    or normalized_memory
                    in normalized_query
                ):

                    partial_matches.append(
                        (
                            memory_id,
                            memory_content,
                        )
                    )

            if partial_matches:

                deleted = 0

                for (
                    memory_id,
                    memory_content,
                ) in partial_matches:

                    if self.memory.forget_by_id(
                        memory_id
                    ):

                        deleted += 1

                if deleted == 1:

                    return (
                        "I forgot the memory about "
                        f"'{content}'."
                    )

                return (
                    f"I forgot {deleted} memories "
                    f"matching '{content}'."
                )

        # ----------------------------------------------------
        # Nothing matched.
        # ----------------------------------------------------

        return (
            "I couldn't find a memory matching "
            f"'{content}'."
        )

    # ========================================================
    # FORGET ALL
    # ========================================================

    def _forget_all(self):

        memories = (
            self.memory.get_memories()
        )

        if not memories:

            return (
                "I don't have any permanent "
                "memories to forget."
            )

        count = len(
            memories
        )

        self.memory.forget()

        return (
            f"I forgot all {count} permanent "
            "memories about you."
        )