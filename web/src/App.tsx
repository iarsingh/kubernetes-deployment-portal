import React, { useState } from "react";

export function App() {
  const [manifest, setManifest] = useState("");
  const [values, setValues] = useState("");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const response = await fetch("/releases", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        name: form.get("name"),
        image: form.get("image"),
        replicas: Number(form.get("replicas")),
        profile: form.get("profile"),
        port: Number(form.get("port")),
      }),
    });
    const body = await response.json();
    if (!response.ok) {
      setError(body.detail);
      setManifest("");
      setValues("");
      return;
    }
    setError("");
    setManifest(body.manifest);
    setValues(body.helm_values);
  }

  return (
    <main>
      <h1>Release</h1>
      <form onSubmit={submit}>
        <input name="name" defaultValue="billing" />
        <input name="image" defaultValue="billing:0.1.0" />
        <input name="replicas" type="number" min={1} max={5} defaultValue={2} />
        <select name="profile" defaultValue="small">
          <option value="small">small</option>
          <option value="medium">medium</option>
          <option value="large">large</option>
        </select>
        <input name="port" type="number" defaultValue={8080} />
        <button type="submit">Render</button>
      </form>
      {error && <p role="alert">{error}</p>}
      <h2>Manifest</h2>
      <pre>{manifest}</pre>
      <h2>Helm values</h2>
      <pre>{values}</pre>
    </main>
  );
}
