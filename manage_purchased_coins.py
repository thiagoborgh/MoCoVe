#!/usr/bin/env python3
"""
Script para gerenciar a lista de moedas já compradas
Permite visualizar, adicionar e remover moedas da lista de controle
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_trading_agent_robust import SimpleAgent

def main():
    print("🛡️ === GERENCIADOR DE MOEDAS COMPRADAS ===")
    
    # Criar instância do agente
    agent = SimpleAgent()
    
    while True:
        print("\nOpções disponíveis:")
        print("1. Mostrar moedas compradas")
        print("2. Remover moeda da lista (permitir recompra)")
        print("3. Resetar lista completa")
        print("4. Sair")
        
        choice = input("\nEscolha uma opção (1-4): ").strip()
        
        if choice == "1":
            print("\n📋 Lista atual de moedas compradas:")
            purchased = agent.show_purchased_coins()
            if purchased:
                for i, coin in enumerate(sorted(purchased), 1):
                    print(f"  {i}. {coin}")
            
        elif choice == "2":
            purchased = agent.show_purchased_coins()
            if not purchased:
                print("❌ Nenhuma moeda comprada para remover")
                continue
                
            print("\nMoedas disponíveis para remoção:")
            for i, coin in enumerate(sorted(purchased), 1):
                print(f"  {i}. {coin}")
                
            try:
                index = int(input("Digite o número da moeda para remover: ")) - 1
                coin_to_remove = sorted(purchased)[index]
                if agent.remove_purchased_coin(coin_to_remove):
                    print(f"✅ {coin_to_remove} removida! Agora pode ser comprada novamente.")
            except (ValueError, IndexError):
                print("❌ Opção inválida")
                
        elif choice == "3":
            confirm = input("⚠️ Tem certeza que deseja resetar TODA a lista? (sim/não): ").lower()
            if confirm in ['sim', 's', 'yes', 'y']:
                agent.reset_purchased_coins()
                print("✅ Lista de moedas compradas foi resetada!")
            else:
                print("❌ Operação cancelada")
                
        elif choice == "4":
            print("👋 Saindo...")
            break
            
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main()