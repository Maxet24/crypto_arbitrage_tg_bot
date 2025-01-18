from yoomoney import Client
token = "410018807695183.13886AE9CC1D18BF584891CBEB7641C373D374DA197F67B1AC0CC0784DD72BA61F5D797EFB3185F3ECB7CCB3624F4EE226F8D1771302D862151138A00E8125FD9D805913D6E98065A5C99736E5455DF9467A3615F0E0A20D71371D5411CB077194AAF8EAEB48289B17E6EB96393E6C47D5A586FD9C233B82869757E8D001C8F8"
client = Client(token)
history = client.operation_history(label="105")
print("List of operations:")
print("Next page starts with: ", history.next_record)
for operation in history.operations:
    print()
    print("Operation:",operation.operation_id)
    print("\tStatus     -->", operation.status)
    print("\tDatetime   -->", operation.datetime)
    print("\tTitle      -->", operation.title)
    print("\tPattern id -->", operation.pattern_id)
    print("\tDirection  -->", operation.direction)
    print("\tAmount     -->", operation.amount)
    print("\tLabel      -->", operation.label)
    print("\tType       -->", operation.type)