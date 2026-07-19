# Lancimoun.github.io

Launch-ready source for Lance Jilliard Galicia's portfolio front door.

The site presents the FORGE family as a set of reliability proofs: auditable memory, grounded retrieval, deterministic evaluation, safe automation, and observable failure behavior. Its neural-field motion is implemented with the browser canvas API and has no runtime dependencies.

Status: prepared and committed locally. The public GitHub repository has not been created or published.

## Verify

From this directory:

```powershell
python -m unittest discover -s tests -v
```

From the parent REVIVAL CLAUDE hub:

```powershell
python LOOP\audit_frontend.py --advisory
```

## Preview

Open `index.html` directly, or run a local static server:

```powershell
python -m http.server 8000
```

Then visit `http://localhost:8000`.

## Deployment boundary

Publishing requires Lance to create the public `Lancimoun/Lancimoun.github.io` repository. Until that explicit approval and authenticated action, this repository stays local.
