<script>
    import { onMount } from "svelte";
    import {
        session,
        getSession,
        submitArgument,
        submitAppeal,
    } from "../stores.js";

    export let id;
    let newArgument = "";
    let imageFile;
    let appealContent = "";
    let currentUser = "user1"; // This should be dynamically set based on the current user
    let canAppeal = false;
    let appealSubmitted = false;
    let inviteEmail = "";
    let shareLink = `${window.location.origin}/session/${id}`;
    let messages = [];

    let socket;

    onMount(async () => {
        await getSession(id);

        socket = new WebSocket(`ws://localhost:8000/ws/${id}`);
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.message === "New argument submitted") {
                addMessage(`New argument submitted`);
                if (data.argumentCount === 2) {
                    addMessage(
                        "Both arguments submitted. Waiting for judgement...",
                    );
                }
            } else if (data.message === "Judgement ready") {
                $session.judgement = data.judgement;
                addMessage(
                    `Judgement received: ${data.judgement.winner} wins!`,
                );
                checkAppealEligibility();
            } else if (data.message === "Appeal processed") {
                $session.appeal_judgement = data.appeal_judgement;
                appealSubmitted = true;
                addMessage(
                    `Appeal judgement received: ${data.appeal_judgement.winner} wins!`,
                );
                checkAppealEligibility();
            }
        };
    });

    function checkAppealEligibility() {
        const judgement = $session.judgement;
        const appealJudgement = $session.appeal_judgement;

        if (judgement && !appealJudgement) {
            canAppeal = judgement.loser === currentUser;
        } else if (appealJudgement) {
            canAppeal =
                appealJudgement.loser === currentUser && !appealSubmitted;
        } else {
            canAppeal = false;
        }
    }

    async function handleSubmitArgument(event) {
        event.preventDefault();
        try {
            const result = await submitArgument(id, newArgument, imageFile);
            addMessage(`${currentUser} submitted an argument`);
            newArgument = "";
            imageFile = null;
        } catch (error) {
            console.error("Error submitting argument:", error);
            alert("Failed to submit argument. Please try again.");
        }
    }

    async function handleSubmitAppeal() {
        try {
            await submitAppeal(id, appealContent, currentUser);
            addMessage(`${currentUser} submitted an appeal`);
            appealContent = "";
            appealSubmitted = true;
        } catch (error) {
            console.error("Error submitting appeal:", error);
            alert("Failed to submit appeal. Please try again.");
        }
    }

    async function copyShareLink() {
        try {
            await navigator.clipboard.writeText(shareLink);
            alert("Link copied to clipboard!");
        } catch (err) {
            console.error("Failed to copy: ", err);
        }
    }

    function addMessage(content) {
        messages = [...messages, { content, timestamp: new Date() }];
    }

    $: {
        if ($session) {
            checkAppealEligibility();
        }
    }

    $: canSubmitArgument = $session?.arguments && $session.arguments.length < 2;
    $: canGetJudgement =
        $session?.arguments &&
        $session.arguments.length === 2 &&
        !$session?.judgement;
</script>

<main>
    <h1>{$session?.name || "Loading..."}</h1>
    <p>{$session?.description || "No description available."}</p>

    <section>
        <h2>Debate Chat</h2>
        <div class="chat-box">
            {#each messages as message}
                <p>{message.content}</p>
            {/each}
        </div>
    </section>

    <section>
        <h2>Invite Opponent</h2>
        <p>Share this link with your opponent:</p>
        <div class="share-link">
            <input type="text" readonly value={shareLink} />
            <button on:click={copyShareLink}>Copy Link</button>
        </div>
    </section>

    <section>
        <h2>Arguments</h2>
        {#if $session?.arguments && $session.arguments.length > 0}
            {#each $session.arguments as argument, index}
                <div class="argument">
                    <h3>
                        Argument {index + 1} by {index === 0
                            ? $session.user1_name
                            : $session.user2_name}
                    </h3>
                    <p>{argument.content}</p>
                    {#if argument.image_url}
                        <img src={argument.image_url} alt="Argument image" />
                    {/if}
                </div>
            {/each}
        {:else}
            <p>No arguments submitted yet.</p>
        {/if}
    </section>

    {#if canSubmitArgument}
        <section>
            <h2>Submit Argument</h2>
            <form on:submit|preventDefault={handleSubmitArgument}>
                <div>
                    <label for="argument">Your Argument:</label>
                    <textarea id="argument" bind:value={newArgument} required
                    ></textarea>
                </div>
                <div>
                    <label for="image">Upload Image (optional):</label>
                    <input
                        type="file"
                        id="image"
                        bind:files={imageFile}
                        accept="image/*"
                    />
                </div>
                <button type="submit">Submit Argument</button>
            </form>
        </section>
    {:else if canGetJudgement}
        <section>
            <h2>Waiting for Judgement</h2>
            <p>
                Both arguments have been submitted. The AI judge is now
                evaluating them.
            </p>
        </section>
    {/if}

    {#if $session?.judgement}
        <section>
            <h2>Judgement</h2>
            <div class="judgement">
                <p>
                    <strong>Winner:</strong>
                    {$session.judgement.winner === "Argument 1"
                        ? $session.user1_name
                        : $session.user2_name}
                </p>
                <p>
                    <strong>Winning Argument:</strong>
                    {$session.judgement.winning_argument}
                </p>
                <p>
                    <strong>Loser:</strong>
                    {$session.judgement.loser === "Argument 1"
                        ? $session.user1_name
                        : $session.user2_name}
                </p>
                <p>
                    <strong>Losing Argument:</strong>
                    {$session.judgement.losing_argument}
                </p>
                <p>
                    <strong>Reasoning:</strong>
                    {$session.judgement.reasoning}
                </p>
            </div>
        </section>

        {#if canAppeal}
            <section>
                <h2>Submit Appeal</h2>
                <p>
                    As the losing party, you have the opportunity to appeal this
                    decision. Please provide your appeal argument below:
                </p>
                <form on:submit|preventDefault={handleSubmitAppeal}>
                    <textarea
                        bind:value={appealContent}
                        required
                        placeholder="Enter your appeal argument here..."
                    ></textarea>
                    <button type="submit">Submit Appeal</button>
                </form>
            </section>
        {:else if appealSubmitted}
            <p>Your appeal has been submitted and is being processed.</p>
        {/if}
    {/if}

    {#if $session?.appeal_judgement}
        <section>
            <h2>Appeal Judgement</h2>
            <div class="appeal-judgement">
                <p>
                    <strong>Winner:</strong>
                    {$session.appeal_judgement.winner === "Argument 1"
                        ? $session.user1_name
                        : $session.user2_name}
                </p>
                <p>
                    <strong>Winning Argument:</strong>
                    {$session.appeal_judgement.winning_argument}
                </p>
                <p>
                    <strong>Loser:</strong>
                    {$session.appeal_judgement.loser === "Argument 1"
                        ? $session.user1_name
                        : $session.user2_name}
                </p>
                <p>
                    <strong>Losing Argument:</strong>
                    {$session.appeal_judgement.losing_argument}
                </p>
                <p>
                    <strong>Reasoning:</strong>
                    {$session.appeal_judgement.reasoning}
                </p>
            </div>
        </section>
    {/if}
</main>

<style>
    main {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }

    section {
        margin-bottom: 30px;
    }

    .argument,
    .judgement,
    .appeal-judgement {
        border: 1px solid #ccc;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 5px;
    }

    form {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }

    textarea,
    input[type="email"] {
        width: 100%;
        padding: 10px;
    }

    textarea {
        height: 100px;
    }

    button {
        padding: 10px 15px;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }

    button:hover {
        background-color: #0056b3;
    }

    img {
        max-width: 100%;
        height: auto;
        margin-top: 10px;
    }

    .chat-box {
        height: 300px;
        overflow-y: auto;
        border: 1px solid #ccc;
        padding: 10px;
        margin-bottom: 20px;
    }

    .share-link {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }

    .share-link input {
        flex-grow: 1;
    }
</style>
