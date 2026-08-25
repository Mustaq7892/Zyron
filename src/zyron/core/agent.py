import json
import re

from ..ai.ollama_client import ask_ollama
from .memory import ConversationMemory
from .memory_commands import MemoryCommandHandler


class ZyronAgent:
    """
    Dynamic AI agent for Zyron.

    Architecture:

        User
          |
          v
        Memory
          |
          +---- Explicit memory ----------> Direct memory
          |
          +---- Relevant memory ----------> Direct memory
          |
          v
        Dynamic capability discovery
          |
          +---- No capability ----------> Fast conversation
          |
          +---- Capability found -------> Dynamic planner
                                               |
                                               v
                                          Tool Registry
                                               |
                                               v
                                          Real capability

    Important design principles:

    1. ToolRegistry is the source of truth.
    2. No hard-coded application/command matching.
    3. Normal conversation should avoid the tool planner.
    4. Memory operations should avoid Ollama.
    5. Tool results are returned directly whenever possible.
    6. Only registered tools can be executed.
    7. New tools added to ToolRegistry are automatically
       available to the dynamic agent.
    """

    def __init__(
        self,
        tool_registry,
        memory=None,
        name="User",
    ):
        self.tool_registry = tool_registry

        self.memory = (
            memory
            if memory is not None
            else ConversationMemory()
        )

        self.name = name

        self.memory_commands = MemoryCommandHandler(
            self.memory,
            self.name,
        )

        self._capability_index = None
        self._capability_signature = None

        # Pending destructive action waiting for explicit user confirmation.
        self._pending_confirmation = None

        # Pending tool request waiting for one or more missing arguments.
        self._pending_clarification = None

    # ========================================================
    # UPDATE NAME
    # ========================================================

    def set_name(
        self,
        name,
    ):
        """
        Dynamically update the user's name.
        """

        if name is None:
            return

        name = str(name).strip()

        if not name:
            return

        self.name = name

        self.memory_commands = MemoryCommandHandler(
            self.memory,
            self.name,
        )

    # ========================================================
    # UPDATE MEMORY
    # ========================================================

    def set_memory(
        self,
        memory,
    ):
        """
        Dynamically replace the active memory implementation.
        """

        if memory is None:
            return

        self.memory = memory

        self.memory_commands = MemoryCommandHandler(
            self.memory,
            self.name,
        )

    # ========================================================
    # GET TOOL SCHEMAS
    # ========================================================

    def _get_tool_schemas(
        self,
    ):
        """
        Get the current ToolRegistry descriptions.

        ToolRegistry remains the single source of truth.
        """

        return self.tool_registry.get_descriptions()

    # ========================================================
    # BUILD DYNAMIC CAPABILITY INDEX
    # ========================================================

    def _build_capability_index(
        self,
    ):
        """
        Build a lightweight searchable index from the
        currently registered capabilities.

        Nothing here assumes that specific capabilities
        such as Chrome, CPU, RAM, folders, weather, etc.
        exist.

        Everything comes from ToolRegistry.
        """

        tools = self._get_tool_schemas()

        index = {}

        for name, tool in tools.items():

            description = str(
                tool.get(
                    "description",
                    "",
                )
            ).strip()

            searchable_text = (
                f"{name} {description}"
            ).lower()

            words = set(
                re.findall(
                    r"[a-zA-Z0-9]+",
                    searchable_text,
                )
            )

            index[name] = {
                "name": name,
                "description": description,
                "words": words,
                "parameters": tool.get(
                    "parameters",
                    {},
                ),
            }

        return index

    # ========================================================
    # GET DYNAMIC CAPABILITY INDEX
    # ========================================================

    def _get_capability_index(
        self,
    ):
        """
        Return the current capability index.

        If tools are added or removed from ToolRegistry,
        the index is rebuilt automatically.
        """

        current_names = tuple(
            self.tool_registry.get_names()
        )

        if (
            self._capability_index is None
            or self._capability_signature
            != current_names
        ):
            self._capability_index = (
                self._build_capability_index()
            )

            self._capability_signature = (
                current_names
            )

        return self._capability_index

    # ========================================================
    # FIND CANDIDATE CAPABILITIES
    # ========================================================

    def _find_candidate_capabilities(
        self,
        command,
    ):
        """
        Dynamically identify the strongest registered capabilities.
    
        The matcher uses only ToolRegistry metadata.
    
        Ranking considers:
            - meaningful request words;
            - rare words across registered capabilities;
            - tool-name overlap;
            - phrase overlap;
            - parameter names;
            - explicit action intent;
            - generic content-inspection intent;
            - separation between competing candidates.
    
        The matcher does not contain application-specific rules such as:
    
            "Zyron folder -> list_zyron_files"
    
        Instead, it recognizes the user's intent and compares that
        intent against registered capability metadata.
        """
    
        command = str(command).strip().lower()
    
        if not command:
            return []
    
        command_words_list = re.findall(
            r"[a-zA-Z0-9]+",
            command,
        )
    
        if not command_words_list:
            return []
    
        command_words = set(command_words_list)
    
        # ============================================================
        # GENERAL LANGUAGE WORDS
        # ============================================================
    
        generic_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "to",
            "for",
            "of",
            "in",
            "on",
            "at",
            "with",
            "from",
            "is",
            "am",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "i",
            "me",
            "my",
            "mine",
            "you",
            "your",
            "yours",
            "we",
            "our",
            "ours",
            "they",
            "their",
            "theirs",
            "it",
            "this",
            "that",
            "these",
            "those",
            "what",
            "when",
            "where",
            "who",
            "why",
            "how",
            "do",
            "does",
            "did",
            "can",
            "could",
            "would",
            "should",
            "will",
            "shall",
            "please",
            "hello",
            "hi",
            "hey",
            "zyron",
            "tell",
            "give",
            "want",
            "need",
            "like",
            "something",
            "anything",
            "about",
            "just",
            "help",
            "assist",
            "today",
            "now",
            "use",
            "using",
            "right",
            "called",
            "call",
        }
    
        meaningful_words = (
            command_words
            - generic_words
        )
    
        # ============================================================
        # GENERIC INTENT DETECTION
        # ============================================================
    
        action_words = {
            "open",
            "create",
            "delete",
            "remove",
            "close",
            "launch",
            "start",
            "stop",
            "run",
            "search",
            "find",
            "list",
            "show",
            "get",
            "check",
            "read",
            "write",
            "update",
            "rename",
            "move",
            "copy",
            "download",
            "upload",
            "play",
            "pause",
            "remember",
            "forget",
            "display",
            "inspect",
            "view",
        }
    
        # ------------------------------------------------------------
        # Explicit action intent.
        #
        # We intentionally detect these BEFORE removing generic words
        # so that "show" remains meaningful when it represents an
        # actual user action.
        # ------------------------------------------------------------
    
        explicit_request_actions = (
            command_words.intersection(
                action_words
            )
        )
    
        # ------------------------------------------------------------
        # Content-inspection intent.
        #
        # Examples:
        #
        #   What is in my Zyron folder?
        #   What is inside my Zyron folder?
        #   What does my Zyron folder contain?
        #   Show me what is in the Zyron folder
        #   Show me what's inside Zyron
        #   Display the contents of my folder
        #
        # This is generic intent detection. It does not mention
        # list_zyron_files or any other specific tool.
        # ------------------------------------------------------------
    
        content_inspection = (
            bool(
                re.search(
                    r"\bwhat\s+(?:is|are)\s+(?:in|inside)\b",
                    command,
                    flags=re.IGNORECASE,
                )
            )
            or bool(
                re.search(
                    r"\bwhat\s+does\s+.+?\s+contain\b",
                    command,
                    flags=re.IGNORECASE,
                )
            )
            or bool(
                re.search(
                    r"\bwhat\s+.+?\s+contain\b",
                    command,
                    flags=re.IGNORECASE,
                )
            )
            or bool(
                re.search(
                    r"\bcontents?\s+of\b",
                    command,
                    flags=re.IGNORECASE,
                )
            )
            or bool(
                re.search(
                    r"\bshow\s+me\s+what\s+is\s+(?:in|inside)\b",
                    command,
                    flags=re.IGNORECASE,
                )
            )
            or bool(
                re.search(
                    r"\bshow\s+me\s+what\s+.+?\s+(?:is\s+)?(?:in|inside)\b",
                    command,
                    flags=re.IGNORECASE,
                )
            )
            or bool(
                re.search(
                    r"\bshow\s+me\s+.+?\s+(?:inside|in)\b",
                    command,
                    flags=re.IGNORECASE,
                )
            )
        )
    
        # Content inspection semantically behaves like a list/show
        # request, even when the word "list" never appears.
        if content_inspection:
            explicit_request_actions.add(
                "list"
            )
            explicit_request_actions.add(
                "show"
            )
    
        # ============================================================
        # CAPABILITY INDEX
        # ============================================================
    
        index = self._get_capability_index()
    
        if not index:
            return []
    
        # ============================================================
        # DYNAMIC DOCUMENT FREQUENCY
        # ============================================================
    
        document_frequency = {}
    
        for capability in index.values():
    
            capability_words = (
                set(
                    capability.get(
                        "words",
                        set(),
                    )
                )
                - generic_words
            )
    
            for word in capability_words:
                document_frequency[word] = (
                    document_frequency.get(
                        word,
                        0,
                    )
                    + 1
                )
    
        total_tools = max(
            len(index),
            1,
        )
    
        # ============================================================
        # REQUEST PHRASES
        # ============================================================
    
        request_bigrams = {
            f"{left} {right}"
            for left, right in zip(
                command_words_list,
                command_words_list[1:],
            )
        }
    
        scored = []
    
        # ============================================================
        # SCORE EACH REGISTERED CAPABILITY
        # ============================================================
    
        for tool_name, capability in index.items():
    
            capability_words = (
                set(
                    capability.get(
                        "words",
                        set(),
                    )
                )
                - generic_words
            )
    
            if not capability_words:
                continue
    
            # --------------------------------------------------------
            # Tool-name words
            # --------------------------------------------------------
    
            tool_name_words = (
                set(
                    re.findall(
                        r"[a-zA-Z0-9]+",
                        tool_name.lower(),
                    )
                )
                - generic_words
            )
    
            # --------------------------------------------------------
            # Parameter names
            # --------------------------------------------------------
    
            parameter_names = set()
    
            parameters = capability.get(
                "parameters",
                {},
            )
    
            if isinstance(
                parameters,
                dict,
            ):
                for parameter_name in parameters:
                    parameter_names.update(
                        re.findall(
                            r"[a-zA-Z0-9]+",
                            str(
                                parameter_name
                            ).lower(),
                        )
                    )
            # --------------------------------------------------------
            # Argument-shape evidence
            # --------------------------------------------------------
            #
            # Detect whether the user's request contains a filename,
            # path-like value, or extension.
            #
            # This is generic metadata-based evidence. It does not
            # mention any specific filename or specific Zyron tool.
            # --------------------------------------------------------

            filename_like_words = {
                word
                for word in command_words_list
                if (
                    "." in word
                    or "\\" in word
                    or "/" in word
                )
            }

            parameter_argument_match = False

            if filename_like_words:

                parameter_argument_match = bool(
                    parameter_names.intersection(
                        {
                            "file",
                            "filename",
                            "file_name",
                            "path",
                            "filepath",
                            "file_path",
                        }
                    )
                )
            # --------------------------------------------------------
            # Word overlap
            # --------------------------------------------------------
    
            overlap = (
                meaningful_words.intersection(
                    capability_words
                )
            )
    
            name_overlap = (
                meaningful_words.intersection(
                    tool_name_words
                )
            )
    
            parameter_overlap = (
                meaningful_words.intersection(
                    parameter_names
                )
            )
    
            # --------------------------------------------------------
            # Action words registered by the capability
            # --------------------------------------------------------
    
            capability_actions = (
                capability_words.intersection(
                    action_words
                )
            )
    
            action_overlap = (
                explicit_request_actions.intersection(
                    capability_actions
                )
            )
    
            # --------------------------------------------------------
            # Skip capabilities with absolutely no evidence.
            # --------------------------------------------------------
    
            if (
                not overlap
                and not name_overlap
                and not parameter_overlap
                and not action_overlap
            ):
                continue
    
            score = 0.0
    
            # ========================================================
            # NORMAL WORD EVIDENCE
            # ========================================================
    
            for word in overlap:
    
                frequency = document_frequency.get(
                    word,
                    total_tools,
                )
    
                rarity = (
                    total_tools
                    / max(
                        frequency,
                        1,
                    )
                )
    
                score += (
                    1.0
                    + rarity
                )
    
            # ========================================================
            # TOOL NAME EVIDENCE
            # ========================================================
    
            score += (
                len(name_overlap)
                * 7.0
            )
    
            # ========================================================
            # ACTION EVIDENCE
            # ========================================================
    
            # Explicit action agreement is strong.
            score += (
                len(action_overlap)
                * 10.0
            )
    
            # ========================================================
            # CONTENT-INSPECTION BONUS
            # ========================================================
    
            if content_inspection:
    
                # Capabilities whose metadata explicitly describes
                # list/show/display/inspect/view behavior receive a
                # strong generic inspection bonus.
                inspection_actions = {
                    "list",
                    "show",
                    "display",
                    "inspect",
                    "view",
                }
    
                inspection_overlap = (
                    capability_actions.intersection(
                        inspection_actions
                    )
                )
    
                if inspection_overlap:
                    score += (
                        len(
                            inspection_overlap
                        )
                        * 12.0
                    )
    
                # Conversely, an explicit "open" or "create"
                # capability should not win merely because the
                # request contains an object such as "folder".
                conflicting_creation_or_open = (
                    capability_actions.intersection(
                        {
                            "open",
                            "create",
                            "launch",
                        }
                    )
                )
    
                if (
                    conflicting_creation_or_open
                    and not inspection_overlap
                ):
                    score -= (
                        len(
                            conflicting_creation_or_open
                        )
                        * 7.0
                    )
    
            # ========================================================
            # CONFLICTING EXPLICIT ACTION
            # ========================================================

            conflicting_actions = (
                explicit_request_actions
                - capability_actions
            )

            if (
                explicit_request_actions
                and capability_actions
                and not action_overlap
                and conflicting_actions
            ):
                score -= (
                    len(
                        conflicting_actions
                    )
                    * 4.0
                )

            # ========================================================
            # PARAMETER EVIDENCE
            # ========================================================

            score += (
                len(parameter_overlap)
                * 2.0
            )

            # ========================================================
            # ARGUMENT-SHAPE EVIDENCE
            # ========================================================
            #
            # A filename/path-like argument strongly supports a
            # capability whose registered schema accepts a file/path.
            #
            # Example:
            #
            #     Open hello.py
            #
            # should favor a capability requiring "file_name"
            # over a zero-parameter generic folder-opening capability.
            # ========================================================

            if parameter_argument_match:

                score += 12.0
    
            # ========================================================
            # PHRASE EVIDENCE
            # ========================================================
    
            capability_text = (
                f"{tool_name} "
                f"{capability.get('description', '')}"
            ).lower()
    
            capability_words_list = re.findall(
                r"[a-zA-Z0-9]+",
                capability_text,
            )
    
            capability_bigrams = {
                f"{left} {right}"
                for left, right in zip(
                    capability_words_list,
                    capability_words_list[1:],
                )
            }
    
            phrase_overlap = (
                request_bigrams.intersection(
                    capability_bigrams
                )
            )
    
            score += (
                len(phrase_overlap)
                * 2.5
            )
    
            # ========================================================
            # UNIQUE WORD BONUS
            # ========================================================
    
            unique_words = {
                word
                for word in overlap
                if document_frequency.get(
                    word,
                    total_tools,
                )
                == 1
            }
    
            score += (
                len(unique_words)
                * 2.0
            )
    
            # ========================================================
            # STRONG MATCH
            # ========================================================
    
            strong_match = (
                bool(name_overlap)
                or bool(parameter_overlap)
                or bool(unique_words)
                or len(overlap) >= 2
                or bool(action_overlap)
                or bool(parameter_argument_match)
            )
    
            if not strong_match:
                continue
    
            scored.append(
                {
                    "name": tool_name,
                    "score": score,
                    "overlap": overlap,
                    "name_overlap": name_overlap,
                    "parameter_overlap": parameter_overlap,
                    "unique_words": unique_words,
                    "phrase_overlap": phrase_overlap,
                    "action_overlap": action_overlap,
                }
            )
    
        # ============================================================
        # NO CANDIDATES
        # ============================================================

        if not scored:
            return []

        # ============================================================
        # FILE / PATH ARGUMENT PRIORITY
        # ============================================================
        #
        # If the user's request contains a filename or path, prefer
        # a registered capability whose schema explicitly accepts
        # a file/path argument.
        #
        # This is completely metadata-driven.
        #
        # Example:
        #
        #     Open hello.py
        #
        # open_file:
        #     file_name -> required string
        #
        # open_zyron_folder:
        #     no parameters
        #
        # Therefore open_file should win.
        # ============================================================

        filename_like_argument = bool(
            re.search(
                r"(?<![\w.-])[\w.-]+\.[A-Za-z0-9]{1,8}(?![\w.-])",
                command,
                flags=re.IGNORECASE,
            )
        )

        path_like_argument = bool(
            re.search(
                r"(?:^|[\s\"'])"
                r"(?:[A-Za-z]:[\\/]|\.?[\\/])"
                r"[^\\/\s\"']+",
                command,
                flags=re.IGNORECASE,
            )
        )

        if (
            filename_like_argument
            or path_like_argument
        ):

            file_parameter_names = {
                "file",
                "filename",
                "file_name",
                "path",
                "filepath",
                "file_path",
            }

            file_candidates = []

            for item in scored:

                tool = index.get(
                    item["name"]
                )

                if not isinstance(
                    tool,
                    dict,
                ):
                    continue

                parameters = tool.get(
                    "parameters",
                    {},
                )

                if not isinstance(
                    parameters,
                    dict,
                ):
                    continue

                parameter_names_for_tool = {
                    str(parameter_name).lower()
                    for parameter_name in parameters
                }

                if parameter_names_for_tool.intersection(
                    file_parameter_names
                ):
                    file_candidates.append(
                        item
                    )

            if file_candidates:

                file_candidates.sort(
                    key=lambda item: item["score"],
                    reverse=True,
                )

                return [
                    file_candidates[0]["name"]
                ]

        # ============================================================
        # SORT
        # ============================================================
    
        scored.sort(
            key=lambda item: item["score"],
            reverse=True,
        )
    
        best = scored[0]
        best_score = best["score"]
    
        # ============================================================
        # SINGLE CANDIDATE
        # ============================================================
    
        if len(scored) == 1:
            return [
                best["name"]
            ]
    
        second_score = scored[1]["score"]
    
        # ============================================================
        # CLEAR WINNER
        # ============================================================
    
        if best_score >= 5.0 and (
            best_score
            >= second_score * 1.20
            or best_score - second_score
            >= 1.5
        ):
            return [
                best["name"]
            ]
    
        # ============================================================
        # CONTENT INSPECTION SAFETY
        #
        # If the request clearly asks what is inside something,
        # prefer the strongest inspection/list capability instead
        # of allowing unrelated open/create capabilities to compete.
        #
        # This remains metadata-driven.
        # ============================================================
    
        if content_inspection:
    
            inspection_candidates = [
                item
                for item in scored
                if item["action_overlap"].intersection(
                    {
                        "list",
                        "show",
                        "display",
                        "inspect",
                        "view",
                    }
                )
            ]
    
            if inspection_candidates:
    
                inspection_candidates.sort(
                    key=lambda item: item["score"],
                    reverse=True,
                )
    
                return [
                    inspection_candidates[0]["name"]
                ]
    
        # ============================================================
        # DYNAMIC CANDIDATE SET
        # ============================================================

        threshold = max(
            3.0,
            best_score * 0.72,
        )

        qualified_candidates = [
            item
            for item in scored[:2]
            if item["score"] >= threshold
        ]

        # ------------------------------------------------------------
        # Prefer a clear action-specific candidate.
        #
        # Example:
        #
        #     Open hello.py
        #
        # should prefer the file-opening capability over a generic
        # folder-opening capability when both are otherwise close.
        #
        # This remains metadata-driven because the decision uses the
        # action overlap and registered capability metadata.
        # ------------------------------------------------------------

        if len(qualified_candidates) > 1:

            action_matches = [
                item
                for item in qualified_candidates
                if item["action_overlap"]
            ]

            if action_matches:

                action_matches.sort(
                    key=lambda item: item["score"],
                    reverse=True,
                )

                best_action = action_matches[0]

                return [
                    best_action["name"]
                ]

        return [
            item["name"]
            for item in qualified_candidates
        ]
    
    # ========================================================
    # FORMAT TOOLS FOR OLLAMA
    # ========================================================

    def _format_tools_for_prompt(
        self,
        tool_names=None,
    ):
        """
        Convert registered capabilities into a compact
        machine-readable prompt.

        Only selected capabilities are included when
        tool_names is provided.
        """

        tools = self._get_tool_schemas()

        if not tools:
            return (
                "No tools are currently available."
            )

        if tool_names is None:

            selected = tools

        else:

            selected = {
                name: tools[name]
                for name in tool_names
                if name in tools
            }

        if not selected:

            return (
                "No relevant tools were identified."
            )

        lines = []

        for name, tool in selected.items():

            description = str(
                tool.get(
                    "description",
                    "",
                )
            ).strip()

            lines.append(
                f"TOOL: {name}"
            )

            lines.append(
                f"DESCRIPTION: {description}"
            )

            parameters = tool.get(
                "parameters",
                {},
            )

            if parameters:

                lines.append(
                    "PARAMETERS:"
                )

                for (
                    parameter_name,
                    parameter_info,
                ) in parameters.items():

                    parameter_type = (
                        parameter_info.get(
                            "type",
                            "string",
                        )
                    )

                    required = (
                        parameter_info.get(
                            "required",
                            False,
                        )
                    )

                    lines.append(
                        f"- {parameter_name}: "
                        f"{parameter_type}, "
                        f"required={required}"
                    )

            else:

                lines.append(
                    "PARAMETERS: none"
                )

            lines.append("")

        return "\n".join(
            lines
        )

    # ========================================================
    # CREATE DYNAMIC PLAN
    # ========================================================

    def create_plan(
        self,
        command,
        candidate_tools=None,
    ):
        """
        Dynamically decide whether the user request needs
        one or more registered capabilities.

        Only candidate capabilities are supplied to Ollama.
        """

        command = str(
            command
        ).strip()

        if not command:

            return {
                "needs_tools": False,
                "plan": [],
                "response": "",
            }

        tools_text = (
            self._format_tools_for_prompt(
                candidate_tools
            )
        )

        prompt = f"""
You are Zyron's capability planner.

User name:
{self.name}

User request:
{command}

Potential registered capabilities:
{tools_text}

Determine whether the user wants one or more of the
listed capabilities.

Rules:

1. Use only capabilities listed above.
2. Never invent a capability.
3. Never invent parameter names.
4. Never invent, guess, assume, or default parameter values.
5. Use only argument values that are explicitly present in the user's request.
6. If the user clearly requests a capability, select that capability even when one or more required arguments are missing.
7. If a required argument is missing, leave that argument OUT of the arguments object.
8. Do NOT replace a missing argument with a guessed value such as 0, 1, 5, 10, or any other default.
9. Do NOT answer the capability request as ordinary conversation just because an argument is missing.
10. Multiple capabilities may be selected when necessary.
11. If the request is ordinary conversation and does not target a listed capability, do not use a tool.
12. Do not pretend a capability was executed.
13. Return ONLY valid JSON.
14. Do not use Markdown.

IMPORTANT ARGUMENT-GROUNDING RULE:

Every argument value in the plan must be directly grounded in the user's
request.

If the user provides only some required arguments, include only those
provided arguments and leave the other required arguments absent.

Example:

User request:
Calculate 10 multiplied

Capability:
calculate_scaled_value

Required arguments:
- value: integer
- multiplier: integer

Correct output:

{{
    "needs_tools": true,
    "plan": [
        {{
            "tool": "calculate_scaled_value",
            "arguments": {{
                "value": 10
            }}
        }}
    ],
    "response": ""
}}

WRONG output:

{{
    "needs_tools": true,
    "plan": [
        {{
            "tool": "calculate_scaled_value",
            "arguments": {{
                "value": 10,
                "multiplier": 1
            }}
        }}
    ],
    "response": ""
}}

The multiplier was not provided by the user, so it MUST NOT be invented.

ALSO WRONG:

{{
    "needs_tools": false,
    "plan": [],
    "response": "10 multiplied by 5 is 50."
}}

The planner must not invent the answer or pretend the missing argument
was supplied.

If the user says:

Calculate 10 multiplied by 5

then both values are explicitly supplied and the correct plan is:

{{
    "needs_tools": true,
    "plan": [
        {{
            "tool": "calculate_scaled_value",
            "arguments": {{
                "value": 10,
                "multiplier": 5
            }}
        }}
    ],
    "response": ""
}}

If a capability is required:

{{
    "needs_tools": true,
    "plan": [
        {{
            "tool": "registered_tool_name",
            "arguments": {{}}
        }}
    ],
    "response": ""
}}

If no capability is required:

{{
    "needs_tools": false,
    "plan": [],
    "response": "natural conversational response"
}}
"""

        try:

            raw_response = ask_ollama(
                prompt,
                temperature=0.0,
                num_predict=512,
            )

        except Exception as error:

            return {
                "needs_tools": False,
                "plan": [],
                "response": (
                    "I couldn't process the request "
                    f"because the AI planning service "
                    f"failed: {error}"
                ),
            }

        parsed = self._parse_json_response(
            raw_response
        )

        if parsed is None:

            return {
                "needs_tools": False,
                "plan": [],
                "response": str(
                    raw_response
                ).strip(),
            }

        return self._normalize_plan(
            parsed,
            command,
        )

    # ========================================================
    # FAST GENERAL CONVERSATION
    # ========================================================

    def _generate_fast_conversational_response(
        self,
        command,
    ):
        """
        Generate one short Ollama response for ordinary
        conversation.

        Important performance rule:
            - Do not load conversation history here.
            - Do not load permanent memories here.
            - Do not send ToolRegistry metadata here.
            - Do exactly one Ollama generation.

        Memory questions and explicit memory commands are
        handled locally before this method is reached.
        """

        command = str(command).strip()

        if not command:
            return "I didn't hear a command."

        prompt = (
            "You are Zyron, a helpful personal AI assistant.\n"
            f"The user's name is {self.name}.\n"
            "Reply naturally to the user's message.\n"
            "Keep the answer brief and suitable for voice output.\n"
            "Do not claim to have performed actions.\n"
            "Do not invent memories or facts about the user.\n\n"
            f"User: {command}\n"
            "Zyron:"
        )

        try:
            response = ask_ollama(
                prompt,
                temperature=0.3,
                num_predict=64,
            )

            response = str(response).strip()

            if response:
                return response

            return "I'm ready to help. What would you like me to do?"

        except Exception as error:
            return (
                "I'm sorry, I couldn't process that request right now. "
                f"Details: {error}"
            )

    # ========================================================
    # ULTRA-FAST SIMPLE CONVERSATION
    # ========================================================

    def _try_local_simple_conversation(
        self,
        command,
    ):
        """Answer very common conversational phrases locally.

        These phrases do not need an LLM. Anything not recognized
        returns None so the normal Ollama conversation path remains
        available for real questions and open-ended requests.
        """

        text = str(command).strip().lower()
        if not text:
            return None

        normalized = re.sub(
            r"[!?.,]+",
            "",
            text,
        ).strip()

        if re.fullmatch(
            r"(hello|hi|hey)( there)?( zyron)?",
            normalized,
        ):
            return (
                f"Hello {self.name}! I'm here and ready to help. "
                "How can I assist you?"
            )

        if re.fullmatch(
            r"(hello|hi|hey)( zyron)? how are you( doing)?",
            normalized,
        ) or re.fullmatch(
            r"how are you( doing)?( zyron)?",
            normalized,
        ):
            return (
                f"I'm doing well, {self.name}, and I'm ready to help. "
                "What would you like me to do?"
            )

        if re.fullmatch(
            r"(are you there|are you online|are you ready)( zyron)?",
            normalized,
        ) or re.fullmatch(
            r"zyron (are you there|are you online|are you ready)",
            normalized,
        ):
            return (
                f"Yes, {self.name}. I'm here and ready to assist you."
            )

        if re.fullmatch(
            r"(who are you|what are you)( zyron)?",
            normalized,
        ):
            return (
                "I'm Zyron, your local AI assistant. I'm ready to help you."
            )

        if normalized in {
            "thanks",
            "thank you",
            "thanks zyron",
            "thank you zyron",
        }:
            return f"You're welcome, {self.name}."

        if normalized in {
            "bye",
            "goodbye",
            "bye zyron",
            "goodbye zyron",
        }:
            return (
                f"Goodbye, {self.name}. I'll be here when you need me."
            )

        return None

    # ========================================================
    # PARSE JSON RESPONSE
    # ========================================================

    def _parse_json_response(
        self,
        response,
    ):
        """
        Safely parse JSON returned by Ollama.

        Handles:

        - Plain JSON
        - JSON inside Markdown fences
        - JSON surrounded by additional text
        """

        if response is None:
            return None

        text = str(
            response
        ).strip()

        if not text:
            return None

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        text = text.strip()

        try:

            return json.loads(
                text
            )

        except json.JSONDecodeError:

            pass

        start = text.find(
            "{"
        )

        end = text.rfind(
            "}"
        )

        if (
            start >= 0
            and end > start
        ):

            candidate = text[
                start:end + 1
            ]

            try:

                return json.loads(
                    candidate
                )

            except json.JSONDecodeError:

                pass

        return None

    # ========================================================
    # VALIDATE TOOL ARGUMENTS
    # ========================================================

    def _validate_plan_arguments(
        self,
        tool_name,
        arguments,
        command=None,
        allow_missing_required=False,
    ):
        """
        Validate model-generated tool arguments against the
        registered ToolRegistry schema.

        This is intentionally generic.

        The validator does not know specific tool names.
        It uses only the registered tool metadata.
        """

        tool = self.tool_registry.get(
            tool_name
        )

        if tool is None:
            return {
                "valid": False,
                "error": (
                    f"Unknown tool: {tool_name}"
                ),
            }

        if not isinstance(
            arguments,
            dict,
        ):
            return {
                "valid": False,
                "error": (
                    f"Arguments for tool '{tool_name}' "
                    "must be an object."
                ),
            }

        parameters = tool.get(
            "parameters",
            {},
        )

        if not isinstance(
            parameters,
            dict,
        ):
            parameters = {}

        # ----------------------------------------------------
        # Support JSON-Schema object format.
        # ----------------------------------------------------

        if (
            parameters.get("type") == "object"
            and isinstance(
                parameters.get("properties"),
                dict,
            )
        ):
            properties = parameters.get(
                "properties",
                {},
            )

            required_names = set(
                parameters.get(
                    "required",
                    [],
                )
            )

            parameters = {
                name: {
                    **(
                        info
                        if isinstance(
                            info,
                            dict,
                        )
                        else {}
                    ),
                    "required": (
                        name in required_names
                    ),
                }
                for name, info in properties.items()
            }

        # ----------------------------------------------------
        # Reject unknown arguments.
        # ----------------------------------------------------

        unknown_arguments = [
            name
            for name in arguments
            if name not in parameters
        ]

        if unknown_arguments:
            return {
                "valid": False,
                "error": (
                    f"Unknown argument(s) for tool "
                    f"'{tool_name}': "
                    f"{', '.join(unknown_arguments)}"
                ),
            }

        # ----------------------------------------------------
        # Check every registered parameter.
        # ----------------------------------------------------

        for (
            parameter_name,
            parameter_info,
        ) in parameters.items():

            if not isinstance(
                parameter_info,
                dict,
            ):
                parameter_info = {}

            required = bool(
                parameter_info.get(
                    "required",
                    False,
                )
            )

            if (
                required
                and parameter_name not in arguments
                and not allow_missing_required
            ):
                return {
                    "valid": False,
                    "error": (
                        f"Missing required argument "
                        f"'{parameter_name}' for tool "
                        f"'{tool_name}'."
                    ),
                }

        # ----------------------------------------------------
        # Basic type validation.
        # ----------------------------------------------------

        for (
            parameter_name,
            value,
        ) in arguments.items():

            parameter_info = parameters.get(
                parameter_name,
                {},
            )

            if not isinstance(
                parameter_info,
                dict,
            ):
                continue

            parameter_type = parameter_info.get(
                "type",
                "string",
            )

            if (
                parameter_type == "integer"
                and (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                )
            ):
                return {
                    "valid": False,
                    "error": (
                        f"Argument '{parameter_name}' "
                        f"for tool '{tool_name}' "
                        "must be an integer."
                    ),
                }

            if (
                parameter_type == "number"
                and (
                    isinstance(value, bool)
                    or not isinstance(
                        value,
                        (int, float),
                    )
                )
            ):
                return {
                    "valid": False,
                    "error": (
                        f"Argument '{parameter_name}' "
                        f"for tool '{tool_name}' "
                        "must be a number."
                    ),
                }

            if (
                parameter_type == "boolean"
                and not isinstance(
                    value,
                    bool,
                )
            ):
                return {
                    "valid": False,
                    "error": (
                        f"Argument '{parameter_name}' "
                        f"for tool '{tool_name}' "
                        "must be a boolean."
                    ),
                }

            if (
                parameter_type == "string"
                and not isinstance(
                    value,
                    str,
                )
            ):
                return {
                    "valid": False,
                    "error": (
                        f"Argument '{parameter_name}' "
                        f"for tool '{tool_name}' "
                        "must be a string."
                    ),
                }

        # ----------------------------------------------------
        # Ground numeric arguments against the user's command.
        #
        # This prevents the planner from inventing numeric values
        # that were never supplied by the user.
        # ----------------------------------------------------

        if not self._numeric_arguments_are_grounded(
            arguments,
            command,
            parameters,
        ):
            return {
                "valid": False,
                "error": (
                    f"Numeric argument(s) for tool "
                    f"'{tool_name}' are not grounded "
                    "in the user's command."
                ),
            }

        return {
            "valid": True,
            "error": "",
        }

    # ========================================================
    # GROUND NUMERIC PLAN ARGUMENTS
    # ========================================================

    def _numeric_arguments_are_grounded(
        self,
        arguments,
        command,
        parameters,
    ):
        """
        Check whether planner-generated numeric arguments are
        grounded in the user's original command.

        This is intentionally generic and does not depend on
        any specific tool name.

        The purpose is to prevent the planner from inventing
        numeric defaults such as:

            User: Calculate 10 multiplied
            Planner: multiplier=1

        A numeric argument is considered grounded when its value
        appears as a numeric literal in the user's command.

        String arguments and non-numeric arguments are ignored.
        """

        if not isinstance(
            arguments,
            dict,
        ):
            return False

        command_text = str(
            command
            if command is not None
            else ""
        )

        command_numbers = {
            int(value)
            for value in re.findall(
                r"(?<![A-Za-z0-9_.-])-?\d+(?![A-Za-z0-9_.-])",
                command_text,
            )
        }

        for (
            parameter_name,
            value,
        ) in arguments.items():

            parameter_info = parameters.get(
                parameter_name,
                {},
            )

            if not isinstance(
                parameter_info,
                dict,
            ):
                continue

            parameter_type = parameter_info.get(
                "type",
                "string",
            )

            if parameter_type not in {
                "integer",
                "number",
            }:
                continue

            if isinstance(
                value,
                bool,
            ):
                return False

            if not isinstance(
                value,
                (int, float),
            ):
                return False

            numeric_value = float(
                value
            )

            if numeric_value.is_integer():
                numeric_value = int(
                    numeric_value
                )

            if numeric_value not in command_numbers:
                return False

        return True


    # ========================================================
    # FIND MISSING REQUIRED ARGUMENTS
    # ========================================================

    def _find_missing_required_arguments(
        self,
        tool_name,
        arguments,
    ):
        """
        Find required arguments that are missing from a
        planner-generated tool call.

        This uses only the registered ToolRegistry schema.
        It does not depend on a specific tool name.
        """

        tool = self.tool_registry.get(
            tool_name
        )

        if tool is None:
            return []

        parameters = tool.get(
            "parameters",
            {},
        )

        if not isinstance(
            parameters,
            dict,
        ):
            return []

        # ----------------------------------------------------
        # Support JSON-Schema object format.
        # ----------------------------------------------------

        if (
            parameters.get("type") == "object"
            and isinstance(
                parameters.get("properties"),
                dict,
            )
        ):
            properties = parameters.get(
                "properties",
                {},
            )

            required_names = set(
                parameters.get(
                    "required",
                    [],
                )
            )

            parameters = {
                name: {
                    **(
                        info
                        if isinstance(
                            info,
                            dict,
                        )
                        else {}
                    ),
                    "required": (
                        name in required_names
                    ),
                }
                for name, info in properties.items()
            }

        if not isinstance(
            arguments,
            dict,
        ):
            arguments = {}

        missing = []

        for (
            parameter_name,
            parameter_info,
        ) in parameters.items():

            if not isinstance(
                parameter_info,
                dict,
            ):
                continue

            if not parameter_info.get(
                "required",
                False,
            ):
                continue

            if parameter_name not in arguments:
                missing.append(
                    parameter_name
                )
                continue

            value = arguments.get(
                parameter_name
            )

            if value is None:
                missing.append(
                    parameter_name
                )
                continue

            if (
                isinstance(value, str)
                and not value.strip()
            ):
                missing.append(
                    parameter_name
                )

        return missing


    # ========================================================
    # CREATE MISSING-ARGUMENT CLARIFICATION
    # ========================================================

    def _create_missing_argument_clarification(
        self,
        tool_name,
        missing_arguments,
    ):
        """
        Create a concise clarification request when a tool
        requires arguments that the user did not provide.

        The response is based only on registered parameter names.
        """

        if not missing_arguments:
            return None

        if len(missing_arguments) == 1:
            parameter_name = missing_arguments[0]

            return (
                f"I need the '{parameter_name}' value "
                f"before I can use '{tool_name}'. "
                f"What {parameter_name} should I use?"
            )

        if len(missing_arguments) == 2:
            parameter_text = (
                f"'{missing_arguments[0]}' and "
                f"'{missing_arguments[1]}'"
            )

        else:
            parameter_text = (
                ", ".join(
                    f"'{name}'"
                    for name in missing_arguments[:-1]
                )
                + ", and "
                + f"'{missing_arguments[-1]}'"
            )

        return (
            f"I need {parameter_text} before I can use "
            f"'{tool_name}'. Please provide them."
        )


    # ========================================================
    # FIND UNGROUNDED NUMERIC ARGUMENTS
    # ========================================================

    def _find_ungrounded_numeric_arguments(
        self,
        tool_name,
        arguments,
        command,
    ):
        """
        Find numeric arguments supplied by the planner that were
        not actually supplied by the user.

        These arguments must be treated as missing because the
        planner may have invented a numeric default.
        """

        tool = self.tool_registry.get(
            tool_name
        )

        if tool is None:
            return []

        parameters = tool.get(
            "parameters",
            {},
        )

        if not isinstance(
            parameters,
            dict,
        ):
            return []

        # ----------------------------------------------------
        # Support JSON-Schema object format.
        # ----------------------------------------------------

        if (
            parameters.get("type") == "object"
            and isinstance(
                parameters.get("properties"),
                dict,
            )
        ):
            properties = parameters.get(
                "properties",
                {},
            )

            required_names = set(
                parameters.get(
                    "required",
                    [],
                )
            )

            parameters = {
                name: {
                    **(
                        info
                        if isinstance(
                            info,
                            dict,
                        )
                        else {}
                    ),
                    "required": (
                        name in required_names
                    ),
                }
                for name, info in properties.items()
            }

        command_numbers = {
            int(value)
            for value in re.findall(
                r"(?<![A-Za-z0-9_.-])-?\d+(?![A-Za-z0-9_.-])",
                str(
                    command
                    if command is not None
                    else ""
                ),
            )
        }

        ungrounded = []

        for (
            parameter_name,
            value,
        ) in arguments.items():

            parameter_info = parameters.get(
                parameter_name,
                {},
            )

            if not isinstance(
                parameter_info,
                dict,
            ):
                continue

            parameter_type = parameter_info.get(
                "type",
                "string",
            )

            if parameter_type not in {
                "integer",
                "number",
            }:
                continue

            if isinstance(
                value,
                bool,
            ):
                continue

            if not isinstance(
                value,
                (int, float),
            ):
                continue

            numeric_value = float(
                value
            )

            if numeric_value.is_integer():
                numeric_value = int(
                    numeric_value
                )

            if numeric_value not in command_numbers:
                ungrounded.append(
                    parameter_name
                )

        return ungrounded


    # ========================================================
    # NORMALIZE PLAN
    # ========================================================

    def _normalize_plan(
        self,
        data,
        command=None,
    ):
        """
        Validate the model-generated plan against the
        actual ToolRegistry.

        The model cannot execute arbitrary functions.
        """

        if not isinstance(
            data,
            dict,
        ):

            return {
                "needs_tools": False,
                "plan": [],
                "response": "",
            }

        needs_tools = bool(
            data.get(
                "needs_tools",
                False,
            )
        )

        response = data.get(
            "response",
            "",
        )

        if response is None:
            response = ""

        response = str(
            response
        ).strip()

        raw_plan = data.get(
            "plan",
            [],
        )

        if not isinstance(
            raw_plan,
            list,
        ):

            raw_plan = []

        available_tools = set(
            self.tool_registry.get_names()
        )

        valid_plan = []

        for item in raw_plan:

            if not isinstance(
                item,
                dict,
            ):
                continue

            tool_name = item.get(
                "tool"
            )

            if not tool_name:
                continue

            tool_name = str(
                tool_name
            ).strip()

            if tool_name not in available_tools:
                continue

            arguments = item.get(
                "arguments",
                {},
            )

            if not isinstance(
                arguments,
                dict,
            ):

                arguments = {}

            # ----------------------------------------------------
            # Validate planner-generated arguments against the
            # registered tool schema.
            #
            # This prevents the planner from inventing missing
            # required arguments or supplying invalid arguments.
            # ----------------------------------------------------

            validation = self._validate_plan_arguments(
                tool_name,
                arguments,
                command,
            )

            if not validation.get(
                "valid",
                False,
            ):
                missing_arguments = (
                    self._find_missing_required_arguments(
                        tool_name,
                        arguments,
                    )
                )

                # ------------------------------------------------
                # A planner may invent a numeric value for a
                # required argument.
                #
                # Example:
                #
                # User:
                #     Calculate 10 multiplied
                #
                # Planner:
                #     value=10
                #     multiplier=1
                #
                # "multiplier" exists in the planner output, but
                # the user never supplied it. Treat it as missing.
                # ------------------------------------------------

                ungrounded_arguments = (
                    self._find_ungrounded_numeric_arguments(
                        tool_name,
                        arguments,
                        command,
                    )
                )

                clarification_arguments = list(
                    dict.fromkeys(
                        missing_arguments
                        + ungrounded_arguments
                    )
                )

                if clarification_arguments:
                    # ------------------------------------------------
                    # Store the incomplete request so the user's next
                    # message can supply the missing argument(s).
                    #
                    # Example:
                    #
                    #   User: "Calculate 10 multiplied"
                    #
                    #   Planner:
                    #       value=10
                    #       multiplier=1
                    #
                    #   "multiplier" is not grounded, so it becomes
                    #   a pending clarification rather than being
                    #   silently discarded.
                    # ------------------------------------------------
                    self._pending_clarification = {
                        "command": command,
                        "tool": tool_name,
                        "arguments": dict(arguments),
                        "missing_arguments": clarification_arguments,
                    }

                    return {
                        "needs_tools": False,
                        "plan": [],
                        "response": (
                            self._create_missing_argument_clarification(
                                tool_name,
                                clarification_arguments,
                            )
                            or ""
                        ),
                    }

                continue

            valid_plan.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                }
            )

        if not valid_plan:

            needs_tools = False

        return {
            "needs_tools": needs_tools,
            "plan": valid_plan,
            "response": response,
        }

    # ========================================================
    # EXECUTE PLAN
    # ========================================================

    def execute_plan(
        self,
        plan,
    ):
        """
        Execute only registered capabilities.
        """

        if not isinstance(
            plan,
            dict,
        ):

            return []

        steps = plan.get(
            "plan",
            [],
        )

        if not isinstance(
            steps,
            list,
        ):

            return []

        results = []

        for step in steps:

            if not isinstance(
                step,
                dict,
            ):
                continue

            tool_name = step.get(
                "tool"
            )

            arguments = step.get(
                "arguments",
                {},
            )

            if not tool_name:
                continue

            if not isinstance(
                arguments,
                dict,
            ):

                arguments = {}

            print(
                f"[Zyron is using tool: {tool_name}]"
            )

            result = (
                self.tool_registry.execute(
                    tool_name,
                    **arguments,
                )
            )

            results.append(
                {
                    "tool": tool_name,
                    "result": result,
                }
            )

        return results

    # ========================================================
    # CREATE FINAL TOOL RESPONSE
    # ========================================================

    def create_final_response(
        self,
        command,
        plan,
        results,
    ):
        """
        Return actual capability results.

        Deterministic results are not unnecessarily sent
        through Ollama again.
        """

        if not results:

            response = plan.get(
                "response",
                "",
            )

            if response:
                return response

            return (
                "I couldn't complete "
                "the requested operation."
            )

        successful_results = []
        failed_results = []

        for item in results:

            result_data = item.get(
                "result",
                {},
            )

            if not isinstance(
                result_data,
                dict,
            ):

                successful_results.append(
                    result_data
                )

                continue

            if result_data.get(
                "success",
                False,
            ):

                successful_results.append(
                    result_data.get(
                        "result",
                        "",
                    )
                )

            else:

                failed_results.append(
                    result_data.get(
                        "error",
                        "Unknown error.",
                    )
                )

        if (
            failed_results
            and not successful_results
        ):

            return (
                "I couldn't complete the request. "
                + " ".join(
                    str(error)
                    for error in failed_results
                )
            )

        responses = []

        for result in successful_results:

            if result is None:
                continue

            if isinstance(
                result,
                str,
            ):

                text = result.strip()

                if text:
                    responses.append(
                        text
                    )

            elif isinstance(
                result,
                (
                    int,
                    float,
                    bool,
                ),
            ):

                responses.append(
                    str(result)
                )

            else:

                try:

                    responses.append(
                        json.dumps(
                            result,
                            indent=2,
                            ensure_ascii=False,
                        )
                    )

                except Exception:

                    responses.append(
                        str(result)
                    )

        if responses:

            final_response = (
                "\n\n".join(
                    responses
                )
            )

            if failed_results:

                final_response += (
                    "\n\nSome parts of the "
                    "request could not be "
                    "completed: "
                    + " ".join(
                        str(error)
                        for error in failed_results
                    )
                )

            return final_response

        return (
            "The requested task "
            "was completed."
        )

    # ========================================================
    # DIRECT MEMORY RESPONSE
    # ========================================================

    def _answer_from_permanent_memory(
        self,
        memories,
    ):
        """
        Return verified permanent memories directly.

        No Ollama call.
        """

        if not memories:

            return (
                "I don't currently have any matching "
                "memories about you."
            )

        lines = [
            "Here is what I currently remember about you:"
        ]

        for memory in memories:

            memory = str(
                memory
            ).strip()

            if not memory:
                continue

            lines.append(
                f"- {memory}"
            )

        if len(lines) == 1:

            return (
                "I don't currently have any matching "
                "memories about you."
            )

        return "\n".join(
            lines
        )

    # ========================================================
    # FIND RELEVANT MEMORIES
    # ========================================================

    def _find_relevant_memories(
        self,
        command,
    ):
        """
        Search permanent memories locally.

        No Ollama call is required.
        """

        try:

            if not hasattr(
                self.memory,
                "get_memories",
            ):

                return []

            rows = self.memory.get_memories()

            if not rows:
                return []

            command = str(
                command
            ).strip()

            command_lower = (
                command.lower()
            )

            # ------------------------------------------------
            # Broad memory questions.
            # ------------------------------------------------

            broad_memory_request = any(
                phrase in command_lower
                for phrase in (
                    "what do you remember about me",
                    "what do you remember",
                    "what can you remember about me",
                    "what memories do you have",
                    "what do you know about me",
                    "tell me what you remember about me",
                )
            )

            if broad_memory_request:

                memories = []

                for row in rows:

                    if (
                        not row
                        or len(row) < 2
                    ):
                        continue

                    text = str(
                        row[1]
                    ).strip()

                    if text:
                        memories.append(
                            text
                        )

                return memories[:20]

            # ------------------------------------------------
            # Words that should not participate in memory
            # matching.
            # ------------------------------------------------

            stop_words = {
                "a",
                "an",
                "and",
                "are",
                "am",
                "be",
                "can",
                "could",
                "did",
                "do",
                "does",
                "for",
                "from",
                "get",
                "give",
                "has",
                "have",
                "how",
                "i",
                "in",
                "is",
                "it",
                "me",
                "my",
                "of",
                "please",
                "remember",
                "tell",
                "that",
                "the",
                "this",
                "to",
                "was",
                "what",
                "when",
                "where",
                "which",
                "who",
                "why",
                "with",
                "you",
                "your",
                "know",
                "about",
                "something",
                "anything",
                "favorite",
                "prefer",
                "preference",
                "like",
            }

            command_words = set(
                word.lower()
                for word in re.findall(
                    r"[a-zA-Z0-9]+",
                    command,
                )
                if (
                    len(word) >= 3
                    and word.lower()
                    not in stop_words
                )
            )

            memory_intent = any(
                phrase in command_lower
                for phrase in (
                    "favorite",
                    "prefer",
                    "preference",
                    "remember",
                    "memory",
                    "know about me",
                    "my project",
                    "my goal",
                    "my name",
                )
            )

            matches = []

            for row in rows:

                if (
                    not row
                    or len(row) < 2
                ):
                    continue

                memory_text = str(
                    row[1]
                ).strip()

                if not memory_text:
                    continue

                memory_words = set(
                    word.lower()
                    for word in re.findall(
                        r"[a-zA-Z0-9]+",
                        memory_text,
                    )
                    if (
                        len(word) >= 3
                        and word.lower()
                        not in stop_words
                    )
                )

                overlap = (
                    command_words
                    .intersection(
                        memory_words
                    )
                )

                normalized_command = (
                    " ".join(
                        re.findall(
                            r"[a-zA-Z0-9]+",
                            command_lower,
                        )
                    )
                )

                normalized_memory = (
                    " ".join(
                        re.findall(
                            r"[a-zA-Z0-9]+",
                            memory_text.lower(),
                        )
                    )
                )

                if (
                    normalized_memory
                    and normalized_memory
                    in normalized_command
                ):

                    matches.append(
                        memory_text
                    )

                    continue

                if len(overlap) >= 2:

                    matches.append(
                        memory_text
                    )

                    continue

                if (
                    memory_intent
                    and any(
                        len(word) >= 5
                        for word in overlap
                    )
                ):

                    matches.append(
                        memory_text
                    )

            return matches[:5]

        except Exception:

            return []

    # ========================================================
    # STORE CONVERSATION
    # ========================================================

    def _remember(
        self,
        command,
        response,
    ):
        """
        Store normal conversation history.

        This is conversation history, not permanent memory.
        """

        try:

            if hasattr(
                self.memory,
                "add",
            ):

                self.memory.add(
                    "user",
                    command,
                )

                self.memory.add(
                    "assistant",
                    response,
                )

        except Exception:

            pass


    def _is_multi_step_command(
        self,
        command,
    ):
        """
        Return True when the user's request contains multiple
        sequential actions.

        Multi-step requests must be handled by create_plan()
        rather than the single-tool direct fast-path.

        Examples:

            Create a folder called Test and then list the files.

            Open Chrome and then open Notepad.

            Create a folder followed by listing the Zyron folder.

            First create the folder, then list its contents.
        """

        command = str(
            command
        ).strip().lower()

        if not command:
            return False

        multi_step_patterns = [
            r"\band\s+then\b",
            r"\bthen\b",
            r"\bfollowed\s+by\b",
            r"\bafter\s+that\b",
            r"\bfirst\b.+\bthen\b",
            r"\bafter\b.+\bthen\b",
        ]

        for pattern in multi_step_patterns:

            if re.search(
                pattern,
                command,
                flags=re.IGNORECASE,
            ):
                return True

        return False


    # ========================================================
    # DYNAMIC DIRECT TOOL FAST-PATH
    # ========================================================


    def _try_direct_single_string_tool(
        self,
        command,
        candidate_tools,
    ):
        """
        Dynamically execute a capability without unnecessary
        Ollama planning.

        Fast paths:

        1. Zero-parameter tools.
           Example:
               open_zyron_folder

        2. One required string parameter.
           The parameter name does NOT need to be hard-coded.

           Examples:
               query
               command
               folder_name
               path
               application

        The actual parameter schema comes from ToolRegistry.

        This method does not contain application-specific rules.
        """

        # ----------------------------------------------------
        # Validate candidate list
        # ----------------------------------------------------

        if not isinstance(
            candidate_tools,
            list,
        ):
            return None

        # We only use the direct fast path when exactly
        # one capability is the strongest candidate.
        if len(candidate_tools) != 1:
            return None

        tool_name = candidate_tools[0]

        # ----------------------------------------------------
        # Get registered tool
        # ----------------------------------------------------

        tool = self.tool_registry.get(
            tool_name
        )

        if not tool:
            return None

        # Destructive/irreversible tools must never execute through the
        # direct fast-path. They must go through the confirmation flow.
        if tool.get(
            "requires_confirmation",
            False,
        ):
            return None

        # ----------------------------------------------------
        # Get parameter schema
        # ----------------------------------------------------

        parameters = tool.get(
            "parameters",
            {},
        )

        if not isinstance(
            parameters,
            dict,
        ):
            return None

        # Support both parameter-schema formats used by tools:
        #
        # 1. Flat internal format:
        #    {"folder_name": {"type": "string", "required": True}}
        #
        # 2. JSON-Schema object format:
        #    {"type": "object",
        #     "properties": {...},
        #     "required": ["folder_name"]}
        #
        # Normalize format 2 into the same internal representation so
        # the direct fast path can execute tools such as create_folder
        # without falling back to the slower Ollama planner.
        if (
            parameters.get("type") == "object"
            and isinstance(parameters.get("properties"), dict)
        ):
            properties = parameters.get("properties", {})
            required_names = set(
                parameters.get("required", [])
            )

            parameters = {
                name: {
                    **(info if isinstance(info, dict) else {}),
                    "required": name in required_names,
                }
                for name, info in properties.items()
            }

        # ====================================================
        # FAST PATH 1
        # ZERO-PARAMETER TOOL
        # ====================================================

        if len(parameters) == 0:

            print(
                f"[Zyron is using tool: {tool_name}]"
            )

            result = self.tool_registry.execute(
                tool_name
            )

            # ------------------------------------------------
            # Handle non-dictionary result
            # ------------------------------------------------

            if not isinstance(
                result,
                dict,
            ):
                return str(result)

            # ------------------------------------------------
            # Successful execution
            # ------------------------------------------------

            if result.get(
                "success",
                False,
            ):

                value = result.get(
                    "result",
                    "",
                )

                if value is None:
                    return ""

                return str(
                    value
                ).strip()

            # ------------------------------------------------
            # Failed execution
            # ------------------------------------------------

            return (
                "I couldn't complete the request. "
                + str(
                    result.get(
                        "error",
                        "Unknown error.",
                    )
                )
            )

        # ====================================================
        # FAST PATH 2
        # EXACTLY ONE REQUIRED STRING PARAMETER
        # ====================================================

        if len(parameters) != 1:
            return None

        parameter_name, parameter_info = next(
            iter(
                parameters.items()
            )
        )

        if not isinstance(
            parameter_info,
            dict,
        ):
            return None

        # ----------------------------------------------------
        # Parameter must be a string
        # ----------------------------------------------------

        if parameter_info.get(
            "type"
        ) != "string":
            return None

        # ----------------------------------------------------
        # Parameter must be required
        # ----------------------------------------------------

        if not parameter_info.get(
            "required",
            False,
        ):
            return None

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # We no longer restrict the parameter name to:
        #     query
        #     command
        #
        # Any single required string parameter can qualify.
        #
        # This makes the fast path dynamic.
        # ----------------------------------------------------

        # ====================================================
        # EXTRACT ARGUMENT FROM NATURAL LANGUAGE
        # ====================================================

        argument_value = self._extract_single_string_argument(
            command,
            tool_name,
            parameter_name,
        )

        if argument_value is None:
            return None

        argument_value = str(
            argument_value
        ).strip()

        if not argument_value:
            return None

        # ====================================================
        # EXECUTE TOOL
        # ====================================================

        print(
            f"[Zyron is using tool: {tool_name}]"
        )

        result = self.tool_registry.execute(
            tool_name,
            **{
                parameter_name: argument_value
            }
        )

        # ----------------------------------------------------
        # Handle non-dictionary result
        # ----------------------------------------------------

        if not isinstance(
            result,
            dict,
        ):
            return str(result)

        # ----------------------------------------------------
        # Successful execution
        # ----------------------------------------------------

        if result.get(
            "success",
            False,
        ):

            value = result.get(
                "result",
                "",
            )

            if value is None:
                return ""

            return str(
                value
            ).strip()

        # ----------------------------------------------------
        # Failed execution
        # ----------------------------------------------------

        return (
            "I couldn't complete the request. "
            + str(
                result.get(
                    "error",
                    "Unknown error.",
                )
            )
        )

    # ========================================================
    # EXTRACT SINGLE STRING TOOL ARGUMENT
    # ========================================================

    def _extract_single_string_argument(
        self,
        command,
        tool_name,
        parameter_name,
    ):
        """
        Dynamically extract the argument for a tool that has
        exactly one required string parameter.

        The extraction is based on the registered parameter
        schema and the natural-language structure of the
        user's command.

        Examples:

            Create a folder called TestFolder
                -> TestFolder

            Create a folder named MyFolder
                -> MyFolder

            Open Chrome
                -> Chrome

            Read hello.py
                -> hello.py

            Read notes.md
                -> notes.md
        """

        command = str(
            command
        ).strip()

        if not command:
            return None

        parameter_name = str(
            parameter_name
        ).strip().lower()

        # ----------------------------------------------------
        # Generic natural-language parameters
        # ----------------------------------------------------

        if parameter_name in {
            "query",
            "command",
            "request",
            "text",
            "prompt",
        }:
            return command

        # ----------------------------------------------------
        # Prefer filename-like arguments when the command
        # contains an obvious file name.
        #
        # Examples:
        #
        #     Read notes.md
        #     Can you show me what is written in notes.md?
        #     Please read hello.py
        #
        # -> notes.md / hello.py
        #
        # This is generic and does not depend on a specific
        # filename.
        # ----------------------------------------------------

        filename_matches = re.findall(
            r"(?<![a-zA-Z0-9_.-])[a-zA-Z0-9_.-]+\.[a-zA-Z0-9]{1,10}(?![a-zA-Z0-9_.-])",
            command,
        )

        if filename_matches:
            return filename_matches[-1].rstrip(
                ".,!?;:"
            )

        # ----------------------------------------------------
        # Try explicit argument markers first.
        # ----------------------------------------------------

        patterns = [
            r"\bcalled\s+['\"]?(.+?)['\"]?\s*$",
            r"\bnamed\s+['\"]?(.+?)['\"]?\s*$",
            r"\bfor\s+['\"]?(.+?)['\"]?\s*$",
            r"\bto\s+['\"]?(.+?)['\"]?\s*$",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                command,
                flags=re.IGNORECASE,
            )

            if match:

                value = match.group(
                    1
                ).strip()

                value = value.strip(
                    "\"'"
                ).strip()

                value = value.rstrip(
                    ".,!?;:"
                )

                if value:
                    return value

        # ----------------------------------------------------
        # Generic fallback.
        #
        # Remove common natural-language action words.
        # The remaining meaningful token becomes the argument.
        # ----------------------------------------------------

        words = re.findall(
            r"[a-zA-Z0-9_.\\-]+",
            command,
        )

        if not words:
            return None

        generic_action_words = {
            "open",
            "read",
            "create",
            "make",
            "new",
            "delete",
            "remove",
            "erase",
            "close",
            "launch",
            "start",
            "stop",
            "run",
            "show",
            "display",
            "view",
            "see",
            "inspect",
            "get",
            "check",
            "find",
            "search",
            "use",
            "please",
            "can",
            "you",
            "could",
            "would",
            "zyron",
            "the",
            "a",
            "an",
            "my",
            "me",
            "file",
            "folder",
            "contents",
            "content",
        }

        remaining_words = [
            word
            for word in words
            if word.lower()
            not in generic_action_words
        ]

        # ----------------------------------------------------
        # Exactly one meaningful token.
        # ----------------------------------------------------

        if len(remaining_words) == 1:

            return remaining_words[0]

        # ----------------------------------------------------
        # Multiple remaining words are ambiguous.
        #
        # Do not guess the argument. Returning None allows the
        # planner to determine the correct argument from the
        # tool description and the user's request.
        # ----------------------------------------------------

        if len(remaining_words) > 1:
            return None

        # ----------------------------------------------------
        # Cannot safely determine the argument.
        # ----------------------------------------------------

        return None

    # ========================================================
    # CONFIRMATION SUPPORT
    # ========================================================

    def _plan_requires_confirmation(
        self,
        plan,
    ):
        """Return True when any planned tool requires confirmation."""

        if not isinstance(plan, dict):
            return False

        steps = plan.get("plan", [])

        if not isinstance(steps, list):
            return False

        for step in steps:

            if not isinstance(step, dict):
                continue

            tool_name = step.get("tool")

            if not tool_name:
                continue

            tool = self.tool_registry.get(tool_name)

            if isinstance(tool, dict) and tool.get(
                "requires_confirmation",
                False,
            ):
                return True

        return False

    # ========================================================
    # CLARIFICATION REPLY
    # ========================================================

    def _clarification_reply(
        self,
        command,
    ):
        """
        Handle a user reply to a pending missing-argument request.

        The pending state stores the original command, tool name,
        current arguments, and missing required arguments.
        """

        if self._pending_clarification is None:
            return None

        pending = self._pending_clarification

        text = str(
            command
        ).strip()

        if not text:
            return (
                "Please provide a value for the missing argument."
            )

        normalized = re.sub(
            r"[!?.,]+",
            "",
            text.lower(),
        ).strip()

        cancel_replies = {
            "cancel",
            "cancel it",
            "stop",
            "never mind",
            "nevermind",
            "forget it",
        }

        if normalized in cancel_replies:
            self._pending_clarification = None

            return (
                "Okay. I cancelled the pending request."
            )

        tool_name = pending.get(
            "tool",
            "",
        )

        arguments = pending.get(
            "arguments",
            {},
        )

        missing_arguments = pending.get(
            "missing_arguments",
            [],
        )

        if not isinstance(
            arguments,
            dict,
        ):
            arguments = {}

        if not isinstance(
            missing_arguments,
            list,
        ):
            missing_arguments = []

        if not tool_name or not missing_arguments:
            self._pending_clarification = None
            return None

        parameter_name = missing_arguments[0]

        candidate_arguments = dict(
            arguments
        )

        candidate_arguments[
            parameter_name
        ] = text

        tool = self.tool_registry.get(
            tool_name
        )

        if tool is None:
            self._pending_clarification = None

            return (
                f"I can no longer find the '{tool_name}' capability."
            )

        parameters = tool.get(
            "parameters",
            {},
        )

        if not isinstance(
            parameters,
            dict,
        ):
            parameters = {}

        parameter_info = parameters.get(
            parameter_name,
            {},
        )

        if not isinstance(
            parameter_info,
            dict,
        ):
            parameter_info = {}

        parameter_type = parameter_info.get(
            "type",
            "string",
        )

        converted_value = text

        if parameter_type == "integer":
            try:
                converted_value = int(text)
            except ValueError:
                return (
                    f"The '{parameter_name}' value must be an integer. "
                    f"Please provide a valid integer."
                )

        elif parameter_type == "number":
            try:
                converted_value = float(text)
            except ValueError:
                return (
                    f"The '{parameter_name}' value must be a number. "
                    f"Please provide a valid number."
                )

        elif parameter_type == "boolean":
            if normalized in {
                "true",
                "yes",
                "y",
            }:
                converted_value = True

            elif normalized in {
                "false",
                "no",
                "n",
            }:
                converted_value = False

            else:
                return (
                    f"The '{parameter_name}' value must be true or false."
                )

        candidate_arguments[
            parameter_name
        ] = converted_value

        # Validate against the complete conversational context.
        #
        # The original command may not contain the missing argument.
        # The user's current clarification supplies that value.
        #
        # Example:
        #
        #   Original:  "Calculate 10 multiplied"
        #   Reply:     "5"
        #
        # The numeric grounding layer must therefore see:
        #
        #   "Calculate 10 multiplied 5"
        #
        # This still satisfies the grounding rule because both values
        # came directly from the user's messages.
        validation_command = (
            str(
                pending.get(
                    "command",
                    "",
                )
            ).strip()
            + " "
            + text
        ).strip()

        validation = self._validate_plan_arguments(
            tool_name,
            candidate_arguments,
            validation_command,
            allow_missing_required=True,
        )

        if not validation.get(
            "valid",
            False,
        ):
            error = validation.get(
                "error",
                "",
            )

            return (
                f"I couldn't use that value for "
                f"'{parameter_name}': {error}"
            )

        remaining_missing = (
            self._find_missing_required_arguments(
                tool_name,
                candidate_arguments,
            )
        )

        if remaining_missing:
            self._pending_clarification = {
                "command": pending.get(
                    "command",
                    "",
                ),
                "tool": tool_name,
                "arguments": candidate_arguments,
                "missing_arguments": remaining_missing,
            }

            return (
                self._create_missing_argument_clarification(
                    tool_name,
                    remaining_missing,
                )
                or ""
            )

        self._pending_clarification = None

        plan = {
            "needs_tools": True,
            "plan": [
                {
                    "tool": tool_name,
                    "arguments": candidate_arguments,
                }
            ],
            "response": "",
        }

        if self._plan_requires_confirmation(
            plan
        ):
            self._pending_confirmation = {
                "command": pending.get(
                    "command",
                    "",
                ),
                "plan": plan,
            }

            return (
                "This action requires your confirmation before I "
                "execute it. Would you like me to continue? "
                "Please reply yes or no."
            )

        results = self.execute_plan(
            plan
        )

        response = self.create_final_response(
            pending.get(
                "command",
                "",
            ),
            plan,
            results,
        )

        self._remember(
            command,
            response,
        )

        return response


    def _confirmation_reply(
        self,
        command,
    ):
        """Handle a yes/no reply for a pending destructive action."""

        if self._pending_confirmation is None:
            return None

        text = re.sub(
            r"[!?.,]+",
            "",
            str(command).strip().lower(),
        ).strip()

        yes_replies = {
            "yes",
            "y",
            "yeah",
            "yep",
            "sure",
            "okay",
            "ok",
            "do it",
            "go ahead",
            "yes please",
            "please do",
        }

        no_replies = {
            "no",
            "n",
            "nope",
            "cancel",
            "cancel it",
            "don't",
            "do not",
            "stop",
        }

        pending = self._pending_confirmation

        if text in no_replies:
            self._pending_confirmation = None
            return (
                "Okay. I cancelled the pending action."
            )

        if text not in yes_replies:
            return (
                "I have a pending action that requires your confirmation. "
                "Please reply yes to continue or no to cancel."
            )

        self._pending_confirmation = None

        results = self.execute_plan(
            pending["plan"]
        )

        response = self.create_final_response(
            pending["command"],
            pending["plan"],
            results,
        )

        self._remember(
            command,
            response,
        )

        return response

    # ========================================================
    # MAIN PROCESS
    # ========================================================

    def process(
        self,
        command,
    ):
        """
        Main dynamic execution pipeline.

        Destructive tools are never executed immediately. If a planned
        tool is marked ``requires_confirmation`` in ToolRegistry, the
        plan is stored and Zyron asks the user for an explicit yes/no.
        """

        command = str(
            command
        ).strip()

        if not command:

            return (
                "I didn't hear a command."
            )

        # ====================================================
        # 1. HANDLE PENDING CONFIRMATION FIRST
        # ====================================================

        confirmation_response = self._confirmation_reply(
            command
        )

        if confirmation_response is not None:
            return confirmation_response

        # ====================================================
        # 1B. HANDLE PENDING ARGUMENT CLARIFICATION
        # ====================================================
        #
        # If Zyron previously asked the user for a missing
        # required argument, the user's next message belongs
        # to that pending request.
        # ====================================================

        clarification_response = self._clarification_reply(
            command
        )

        if clarification_response is not None:
            return clarification_response

        # ====================================================
        # 2. DYNAMIC CAPABILITY DISCOVERY
        # ====================================================

        candidate_tools = (
            self._find_candidate_capabilities(
                command
            )
        )

        # ====================================================
        # 3. EXPLICIT MEMORY COMMAND
        # ====================================================
        #
        # Only allow the memory handler to process the command
        # when no actual registered capability matches it.
        #
        # This prevents commands such as:
        #
        #     Delete the folder DeleteTest
        #
        # from being interpreted as memory requests.

        if not candidate_tools:

            memory_response = (
                self.memory_commands.handle(
                    command
                )
            )

            if memory_response is not None:

                self._remember(
                    command,
                    memory_response,
                )

                return memory_response

        # ====================================================
        # 4. PERMANENT MEMORY LOOKUP
        # ====================================================
        #
        # Only use permanent-memory lookup when no real capability was
        # identified. This prevents requests such as
        # "Delete the folder DeleteTest" from being hijacked by an
        # unrelated memory containing the same words.

        if not candidate_tools:

            relevant_memories = (
                self._find_relevant_memories(
                    command
                )
            )

            if relevant_memories:

                response = (
                    self._answer_from_permanent_memory(
                        relevant_memories
                    )
                )

                self._remember(
                    command,
                    response,
                )

                return response

        # ====================================================
        # 5. ULTRA-FAST SIMPLE CONVERSATION
        # ====================================================

        local_response = self._try_local_simple_conversation(
            command
        )

        if local_response is not None:
            self._remember(
                command,
                local_response,
            )
            return local_response

        # ====================================================
        # 6. NORMAL CONVERSATION
        # ====================================================

        if not candidate_tools:

            response = (
                self._generate_fast_conversational_response(
                    command
                )
            )

            self._remember(
                command,
                response,
            )

            return response

        # ====================================================
        # 7. DYNAMIC DIRECT TOOL FAST-PATH
        # ====================================================

        # Confirmation-required tools are deliberately excluded from
        # this fast path by _try_direct_single_string_tool().

        # ====================================================
        # 7. DYNAMIC DIRECT TOOL FAST-PATH
        # ====================================================
        #
        # The direct fast-path is intended for simple
        # single-action requests.
        #
        # Multi-step requests must go through create_plan()
        # so Ollama can determine the correct execution order.
        #
        # Example:
        #
        #     Create a folder called MultiTest and then
        #     list the contents of my Zyron folder.
        #
        # must NOT execute only list_zyron_files through the
        # direct path.
        # ====================================================

        direct_result = None

        if not self._is_multi_step_command(
            command
        ):

            direct_result = (
                self._try_direct_single_string_tool(
                    command,
                    candidate_tools,
                )
            )

        if direct_result is not None:

            self._remember(
                command,
                direct_result,
            )

            return direct_result

        # ====================================================
        # 8. DYNAMIC CAPABILITY PLANNING
        # ====================================================
        #
        # For multi-step requests, allow the planner to inspect
        # the complete registered tool set.
        #
        # Candidate discovery is intentionally optimized for
        # simple single-action requests, but it may identify
        # only the strongest capability for a multi-action
        # command.
        #
        # Example:
        #
        #     Create a folder called MultiTest and then
        #     list the contents of my Zyron folder.
        #
        # Candidate discovery may return:
        #
        #     ['list_zyron_files']
        #
        # But the planner must be allowed to discover:
        #
        #     create_folder
        #     list_zyron_files
        #
        # Therefore multi-step requests use the complete
        # registered capability set.
        # ====================================================

        if self._is_multi_step_command(
            command
        ):

            plan = self.create_plan(
                command
            )

        else:

            plan = self.create_plan(
                command,
                candidate_tools,
            )

        # ====================================================
        # 9. FALLBACK TO NORMAL CONVERSATION
        # ====================================================

        if not plan.get(
            "needs_tools",
            False,
        ):

            response = plan.get(
                "response",
                "",
            )

            if not response:

                response = (
                    self._generate_fast_conversational_response(
                        command
                    )
                )

            self._remember(
                command,
                response,
            )

            return response

        # ====================================================
        # 10. CONFIRM DESTRUCTIVE TOOLS BEFORE EXECUTION
        # ====================================================

        if self._plan_requires_confirmation(
            plan
        ):

            self._pending_confirmation = {
                "command": command,
                "plan": plan,
            }

            response = (
                "This action requires your confirmation before I "
                "execute it. Would you like me to continue? "
                "Please reply yes or no."
            )

            self._remember(
                command,
                response,
            )

            return response

        # ====================================================
        # 11. EXECUTE SAFE TOOLS
        # ====================================================

        results = self.execute_plan(
            plan
        )

        # ====================================================
        # 12. RETURN TOOL RESULT
        # ====================================================

        response = (
            self.create_final_response(
                command,
                plan,
                results,
            )
        )

        self._remember(
            command,
            response,
        )

        return response
