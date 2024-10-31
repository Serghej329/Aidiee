'''import asyncio

async def operazione_asincrona():
    print("Inizio operazione")
    await asyncio.sleep(1)  
    print("Fine operazione")

async def ciclo_asincrono():
    count = 0
    while count < 5: 
        await operazione_asincrona()
        count += 1
        print(f"Ciclo {count}")

# Avvia l'evento principale
asyncio.run(ciclo_asincrono())
'''