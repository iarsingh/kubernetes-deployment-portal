import React, { useState } from "react";

export function App() {
  const [manifest, setManifest] = useState("");
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const response = await fetch("/releases", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        name: form.get("name"),
        image: form.get("image"),
        replicas: Number(form.get("replicas"))
      })
    });
    const body = await response.json();
    setManifest(body.manifest || body.detail);
  }
  return (
    <main>
      <h1>Release</h1>
      <form onSubmit={submit}>
        <input name="name" defaultValue="billing" />
        <input name="image" defaultValue="billing:0.1.0" />
        <input name="replicas" defaultValue="2" />
        <button type="submit">Render</button>
      </form>
      <pre>{manifest}</pre>
    </main>
  );
}
