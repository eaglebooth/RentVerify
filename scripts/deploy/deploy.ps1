param(
  [string]$ContractPath = "contracts/RentVerify.py"
)

python -c "import ast; ast.parse(open('$ContractPath', encoding='utf-8').read())"
genlayer lint $ContractPath
genlayer deploy $ContractPath --name RentVerify
