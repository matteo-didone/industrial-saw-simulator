# simulator/src/main.py
import asyncio
import logging
from .simulator import IndustrialSawSimulator
from .opcua_server import SawOPCUAServer

async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Industrial Saw Simulator...")

    # Create simulator instance
    simulator = IndustrialSawSimulator()
    
    # Create and initialize OPC UA server
    server = SawOPCUAServer(simulator)
    await server.init()
    
    logging.info("OPC UA Server initialized at opc.tcp://0.0.0.0:4840/saw/")
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        await server.stop()
        logging.info("Server stopped")

if __name__ == "__main__":
    asyncio.run(main())