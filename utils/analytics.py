def calculate_statistics(records):

    total = len(records)

    genuine = sum(
        1
        for record in records
        if record.result == "Likely Original"
    )

    fake = sum(
        1
        for record in records
        if record.result == "Likely Fake"
    )

    suspicious = sum(
        1
        for record in records
        if record.result == "Suspicious"
    )
    not_verified = sum(
        1
        for record in records
        if record.result == "Not Verified"
    )

    if total:

        genuine_percentage = (
            genuine / total
        ) * 100

        fake_percentage = (
            fake / total
        ) * 100

        suspicious_percentage = (
            suspicious / total
        ) * 100
        not_verified_percentage = (
            not_verified / total
        ) * 100

    else:

        genuine_percentage = 0
        fake_percentage = 0
        suspicious_percentage = 0
        not_verified_percentage = 0

    return {

        "total": total,

        "genuine": genuine,

        "fake": fake,

        "suspicious": suspicious,
        "not_verified": not_verified,

        "genuine_percentage":
            round(
                genuine_percentage,
                2
            ),

        "fake_percentage":
            round(
                fake_percentage,
                2
            ),

        "suspicious_percentage":
            round(
                suspicious_percentage,
                2
            ),

        "not_verified_percentage":
            round(
                not_verified_percentage,
                2
            )
    }