"""S08: choose one guardian response with if/else."""


def guardian_response(is_on):
    # TODO: this condition is inverted; repair it after making both predictions.
    if not is_on:
        return "The portal is glowing!"
    else:
        return "The portal is sleeping."


print(guardian_response(False))
print(guardian_response(True))
