# ABB workflow training materials

Use the [Docker package README](../README.md), current handbook and your exercise's student guide. The host needs Docker and approved accounts; language, compiler and browser tools are installed in the image.

**Host terminal**, in the unpacked package folder:

```text
docker compose up -d training
docker compose exec training abb doctor --offline
docker compose exec training abb prepare fw1 demo
docker compose exec --workdir /workspace/work/fw1-demo training bash
```

**Inside the container**:

```bash
pwd
# Expected: /workspace/work/fw1-demo
```

Lab IDs are fw1, fw2, hw1, hw2, t1 and t2. Cases are demo and transfer. Each guide shows its own concrete entry and both fresh transfer paths. Preparation refuses an existing output; resume by re-entering it without preparation. Clean sources remain image-owned. Provider authentication is separate from entering this shell.

The four teaching stages remain demonstration, Markdown abstraction, extraction decisions, then reusable code. Follow the PDF and student guide for allowed changes and acceptance. Instructor and solved validation sources ship only in the facilitator package. All devices and data are synthetic.
