#!/usr/bin/env python3
"""Generate the production-standard v7 Kekang signoff narration."""

from generate_cloned_product_all_narration import MODEL, load_model, process_segment


def main() -> None:
    model = load_model(MODEL)
    process_segment(
        model,
        model.sample_rate,
        "kekang-lingzhi-v7-signoff.json",
    )


if __name__ == "__main__":
    main()
